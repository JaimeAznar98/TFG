from tkinter import N
import model as m
from torch.utils.data import DataLoader
import torch
from torchvision import transforms, models
import torch.nn as nn
import numpy as np
import os
import cv2
import matplotlib.pyplot as plt
import copy


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#device = "cpu"



def train_loop(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    #torch.cuda.empty_cache()
    print(device)
    model.to(device)
    for batch, (X, y) in enumerate(dataloader):
        # Compute prediction and loss
        X = X.to(device)
        y = y.to(device)

        pred = model(X)
        #print('uy')
        loss = loss_fn(pred, y)
        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        

        if batch % 100 == 0:
            loss, current = loss.item(), batch * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")



def test_loop(dataloader, model, loss_fn, best_accuracy):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss, correct = 0, 0
    model.to(device)
    with torch.no_grad():
        for X, y in dataloader:
            X = X.to(device)
            y = y.to(device)


            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()

    test_loss /= num_batches
    correct /= size

    if best_accuracy < correct:
        best_accuracy = correct

    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")

    return best_accuracy


def train(epochs, model, train_split, test_split, loss_fn, optimizer):
    best_accuracy = 0.0
    for epoch in range(epochs):
        train_loop(train_split, model, loss_fn, optimizer)
        print('Test with test split: ')
        acc = test_loop(test_split, model, loss_fn, best_accuracy)

        if acc != best_accuracy:
            best_accuracy = acc
            print(f'change acc: {acc}')
            best_model = copy.deepcopy(model)
        print(f'\n\n\nBest accuracy so far: {best_accuracy}\n\n\n')

    return best_model, best_accuracy




def set_parameter_requires_grad(model, feature_extracting = True):
    if feature_extracting:
        for param in model.parameters():
            param.requires_grad = False


def show_parameter_requires_grad(model, feature_extracting = True):
    if feature_extracting:
        for param in model.parameters():
            if param.requires_grad == True:
                print('yes')





model = models.efficientnet_b0(pretrained=True)

#set_parameter_requires_grad(model)


last = len(model.classifier) -  1

num_features = model.classifier[last].in_features

cont = 0

for param in model.parameters():
    cont += 1 
    if cont < 180:
        param.requires_grad = False

print(cont)
print(num_features)

model.classifier[last] = nn.Linear(num_features,5)

print(model)

epochs = 10

learning_rate = 0.001

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.CenterCrop(224)
    #transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    
])

optimizer = torch.optim.Adam(model.parameters(), lr = learning_rate)

loss_fn = nn.CrossEntropyLoss()

dataset = m.UTKFace(root_dir ='../UTKFace/', transform = transform, extract=2)
train_split, test_split = m.split_dataset(dataset, val_split=0.1)
train_dataloader = DataLoader(train_split, batch_size=32, shuffle=True)
test_dataloader = DataLoader(test_split, batch_size=32, shuffle=False)


cont = 0

for param in model.parameters():
    if param.requires_grad:
        cont += 1

print(f'trainable: {cont}')

best_model, accuracy = train(epochs, model, train_dataloader, test_dataloader, loss_fn, optimizer)

