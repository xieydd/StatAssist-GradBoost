# StatAssist & GradBoost: Classification
StatAssist & GradBoost: A Study on Optimal INT8 Quantization-aware Training from Scratch

## Dataset
- CIFAR10
- CIFAR100
- Imagenet_1K (ILSVRC2015)

## Model
- AlexNet
- VGGNet
- ResNet
- ShuffleNetV2
- MobileNetV2
- MobileNetV3
- MobileNetV3_ReLU

## Run example

- Train

Modify setting/train.json before run.   
```shell
python train.py

```
- Test

Modify setting/evaluate.json before run.   
```shell
python evaluate.py

```

## Latency Check Results (CPU) on Imagenet_1K
* Measured using AMD Ryzen Threadripper 1950X 16-Core Processor, 4 thread & PyTorch 1.6.0

- fbgemm 

| Model   | Params | Flops | Size (FP) | Size(quantized) | Latency(FP) | Latency(quantized)|
|:-------:|:-------:|:-----:|:---------:|:---------------:|------------:|------------------:|
|resnet18 | 11.68 M | 74.02 M| 46.81 MB | 11.78 MB | 366ms  | 245 ms |
|shufflenet_v2_x0_5|  1.36 M | 1.61 M|  5.56 MB | 1.48 MB | 157 ms  | 89 ms |
|shufflenet_v2_x1_0|  2.27 M | 5.87 M|  9.24 MB | 2.44MB | 255 ms  | 372 ms |
|mobilenet_v2_ReLU6|  3.50 M | 12.22 M| 14.21 MB | 3.58 MB | 282 ms  | 143 ms |
|mobilenet_v2_ReLU|  3.50 M | 12.22 M| 14.21 MB | 3.58 MB | 282 ms  | 112 ms |
|mobilenet_v3_large_HS|  5.47 M | 13.83 M|  22.07 MB | 5.81 MB | 286 ms  | 160 ms |
|mobilenet_v3_small_HS| 2.70 M | 5.58 M| 10.91 MB | 2.92 MB | 164 ms  | 99 ms |
|mobilenet_v3_large_ReLU| 5.47 M | 13.83 M| 22.06 MB | 5.57 MB | 258 ms  | 131 ms |
|mobilenet_v3_small_ReLU|2.70 M | 5.58 M| 10.90 MB | 2.77 MB | 148 ms  | 79 ms |

- qnnpack

| Model   | Params | Flops | Size (FP) | Size(quantized) | Latency(FP) | Latency(quantized)|
|:-------:|:-------:|:-----:|:---------:|:---------------:|------------:|------------------:|
|resnet18 | 11.68 M | 74.02 M| 46.81 MB | 11.78 MB | 366ms  | 243 ms |
|shufflenet_v2_x0_5|  1.36 M | 1.61 M|  5.56 MB | 1.48 MB | 157 ms  | 91 ms |
|shufflenet_v2_x1_0|  2.27 M | 5.87 M|  9.24 MB | 2.44MB | 255 ms  | 348 ms |
|mobilenet_v2_ReLU6|  3.50 M | 12.22 M| 14.21 MB | 3.58 MB | 282 ms  | 133 ms |
|mobilenet_v2_ReLU|  3.50 M | 12.22 M| 14.21 MB | 3.58 MB | 282 ms  | 99 ms |
|mobilenet_v3_large_HS|  5.47 M | 13.83 M|  22.07 MB | 5.81 MB | 286 ms  | 151 ms |
|mobilenet_v3_small_HS| 2.70 M | 5.58 M| 10.91 MB | 2.92 MB | 164 ms  | 100 ms |
|mobilenet_v3_large_ReLU| 5.47 M | 13.83 M| 22.06 MB | 5.57 MB | 258 ms  | 123 ms |
|mobilenet_v3_small_ReLU|2.70 M | 5.58 M| 10.90 MB | 2.77 MB | 148 ms  | 77 ms |

