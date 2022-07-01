import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as nnf
# https://pytorch.org/vision/stable/models.html
import torchvision.models as models


class AllergyClassifierModel(nn.Module):
    def __init__(self, weight_file):
        super().__init__()
        convnext = models.convnext_large(pretrained=True)
        self.convnext = nn.Sequential(*list(convnext.children())[:-1])
        self.seq = nn.Sequential(
            LayerNorm2d((1536,), eps=1e-06, elementwise_affine=True),
            nn.Flatten(start_dim=1, end_dim=-1),
            nn.Linear(in_features=1536, out_features=101, bias=True)
        )
        self.out = AllergyLinear(in_features=101, out_features=1,
                                 weight_file=weight_file)

    def forward(self, x):
        x = self.convnext(x)
        x = self.seq(x)
        x = nnf.softmax(x, dim=1)
        x = self.out(x)
        return x
    
    def forward_demo(self, x):
        x = self.convnext(x)
        x = self.seq(x)
        x = nnf.softmax(x, dim=1)
        return x

class LayerNorm2d(nn.LayerNorm):
    def forward(self, x):
        x = x.permute(0, 2, 3, 1)
        x = nnf.layer_norm(
                x, self.normalized_shape, self.weight, self.bias, self.eps)
        x = x.permute(0, 3, 1, 2)
        return x


class AllergyLinear(nn.Module):
    def __init__(self, in_features, out_features, 
                 weight_file='../data/meta/weights.csv'):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features

        weights = np.loadtxt(weight_file, delimiter=',', skiprows=1, 
                             usecols=range(1, 28), dtype='float32')
        self.weight = nn.Parameter(torch.as_tensor(weights.T), 
                                   requires_grad=False)

    def forward(self, x):
        x = nnf.linear(x, self.weight)
        return x