from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import torch
import torch.nn as nn
from torch.autograd import Variable
from functools import reduce
import operator
count_ops = 0
count_params = 0


def get_num_gen(gen):
    return sum(1 for x in gen)


def is_pruned(layer):
    try:
        layer.mask
        return True
    except AttributeError:
        return False


def is_leaf(model):
    return get_num_gen(model.children()) == 0


def get_layer_info(layer):
    layer_str = str(layer)
    type_name = layer_str[:layer_str.find('(')].strip()
    return type_name


def get_layer_param(model):
    return sum([reduce(operator.mul, i.size(), 1) for i in model.parameters()])


### The input batch size should be 1 to call this function
def measure_layer(layer, x):
    global count_ops, count_params
    delta_ops = 0
    delta_params = 0
    multi_add = 1
    type_name = get_layer_info(layer)
    ### ops_conv
    if type_name in ['Conv2d' , 'ConvTranspose2d']:
        out_h = int((x.size()[2] + 2 * layer.padding[0] - layer.dilation[0]*(layer.kernel_size[0] -1) - 1) / layer.stride[0] + 1)
        out_w = int((x.size()[3] + 2 * layer.padding[1] - layer.dilation[1]*(layer.kernel_size[1] -1) - 1) / layer.stride[1] + 1)
        delta_ops = layer.in_channels * layer.out_channels * layer.kernel_size[0] *  \
                layer.kernel_size[1] * out_h * out_w / layer.groups * multi_add
        delta_params = get_layer_param(layer)
        # print(str(layer) + " :" + str(delta_params))

       ### ops_nonlinearity
    elif type_name in ['ReLU', 'PReLU']:
        delta_ops = x.numel()
        delta_params = get_layer_param(layer)

    ### ops_pooling
    elif type_name in ['AvgPool2d']:
        in_w = x.size()[2]
        kernel_ops = layer.kernel_size * layer.kernel_size
        out_w = int((in_w + 2 * layer.padding - layer.kernel_size) / layer.stride + 1)
        out_h = int((in_w + 2 * layer.padding - layer.kernel_size) / layer.stride + 1)
        delta_ops = x.size()[0] * x.size()[1] * out_w * out_h * kernel_ops
        delta_params = get_layer_param(layer)

    elif type_name in ['AdaptiveAvgPool2d']:
        delta_ops = x.size()[0] * x.size()[1] * x.size()[2] * x.size()[3]
        delta_params = get_layer_param(layer)

    ### ops_linear
    elif type_name in ['Linear']:
        weight_ops = layer.weight.numel() * multi_add
        bias_ops = layer.bias.numel()
        delta_ops = x.size()[0] * (weight_ops + bias_ops)
        delta_params = get_layer_param(layer)

    ### ops_nothing
    elif type_name in ['Dropout2d', 'DropChannel', 'Dropout']:
        delta_params = get_layer_param(layer)

    elif type_name in ['BatchNorm2d']:
        delta_params = get_layer_param(layer)
        delta_ops = delta_params

    ### unknown layer type
    # else:
    #     raise TypeError('unknown layer type: %s' % type_name)

    count_ops += delta_ops
    count_params += delta_params
    return


def measure_model(model, H, W):
    global count_ops, count_params
    count_ops = 0
    count_params = 0
    data = Variable(torch.zeros(1, 3, H, W))

    def should_measure(x):
        return is_leaf(x) or is_pruned(x)

    def modify_forward(model):
        for child in model.children():
            if should_measure(child):
                def new_forward(m):
                    def lambda_forward(x):
                        measure_layer(m, x)
                        return m.old_forward(x)
                    return lambda_forward
                child.old_forward = child.forward
                child.forward = new_forward(child)
            else:
                modify_forward(child)

    def restore_forward(model):
        for child in model.children():
            # leaf node
            if is_leaf(child) and hasattr(child, 'old_forward'):
                child.forward = child.old_forward
                child.old_forward = None
            else:
                restore_forward(child)

    modify_forward(model)
    model.forward(data)
    restore_forward(model)

    return count_ops, count_params

def get_scheduler(lrsch, epochs, init_lr, optimizer, restart_ratio):
    if lrsch == "multistep":
        decay1 = epochs // 2
        decay2 = epochs - epochs // 6
        scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[decay1, decay2], gamma=0.5)
    elif lrsch == "step":
        step = epochs // 3
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=step, gamma=0.5)
    elif lrsch == "poly":
        lambda1 = lambda epoch: pow((1 - ((epoch - 1) / epochs)), 0.9)  ## scheduler 2
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=lambda1)  ## scheduler 2
    elif lrsch == "warmpoly":
        scheduler = WarmupPoly(init_lr=init_lr, total_ep=epochs,
                               warmup_ratio=0.05, poly_pow=0.90)
    elif lrsch == "warmpolycycle":
        scheduler = WarmupPolyCycle(init_lr=init_lr, total_ep=epochs,
                               warmup_ratio=0.05, poly_pow=0.90, restart_ratio = restart_ratio)
    return scheduler

class WarmupPoly(object):
    '''
    CLass that defines cyclic learning rate that decays the learning rate linearly till the end of cycle and then restarts
    at the maximum value.
    '''
    def __init__(self, init_lr, total_ep, warmup_ratio=0.05, poly_pow = 0.98):
        super(WarmupPoly, self).__init__()
        self.init_lr = init_lr
        self.total_ep = total_ep
        self.warmup_ep = int(warmup_ratio*total_ep)
        print("warm up learning rate until " + str(self.warmup_ep))
        self.poly_pow = poly_pow

    def get_lr(self, epoch):
        #
        if epoch < self.warmup_ep:
            curr_lr =  self.init_lr*pow((((epoch+1) / self.warmup_ep)), self.poly_pow)

        else:
            curr_lr = self.init_lr*pow((1 - ((epoch- self.warmup_ep)  / (self.total_ep-self.warmup_ep))), self.poly_pow)

        return curr_lr
class WarmupPolyCycle(object):
    '''
    CLass that defines cyclic learning rate that decays the learning rate linearly till the end of cycle and then restarts
    at the maximum value.
    '''
    def __init__(self, init_lr, total_ep, warmup_ratio=0.05, poly_pow = 0.98, restart_ratio = 0.5):
        super(WarmupPolyCycle, self).__init__()
        self.init_lr = init_lr
        self.total_ep = total_ep
        self.restart_cycle = int(self.total_ep*restart_ratio)
        self.restart_ep = self.restart_cycle
        print("restart warmup learning rate from " +str(self.restart_ep))      
        self.warmup_cycle = int(warmup_ratio*self.restart_ep)  
        self.warmup_ep = self.warmup_cycle
        print("warm up learning rate until " + str(self.warmup_ep))
        self.poly_pow = poly_pow

    def get_lr(self, epoch):
        #
        if epoch == self.restart_ep:
            self.warmup_ep = self.restart_ep + self.warmup_cycle
            self.restart_ep = self.restart_ep + self.restart_cycle
            print("restart warmup learning rate from " +str(self.restart_ep))            
            print("warm up learning rate until " + str(self.warmup_ep))
        if epoch < self.warmup_ep:
            curr_lr =  self.init_lr*pow((((epoch+1) / self.warmup_ep)), self.poly_pow)
        else:
            curr_lr = self.init_lr*pow((1 - ((epoch- self.warmup_ep)  / (self.restart_ep-self.warmup_ep))), self.poly_pow)

        return curr_lr

