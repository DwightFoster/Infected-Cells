#Importing librarys
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, datasets, models
import numpy as np

import torch.optim as optim
from torch.utils.data.sampler import SubsetRandomSampler

#Getting test and train loaders
train_data = datasets.ImageFolder(r'Drive/Data', transform=transforms.Compose([transforms.RandomResizedCrop(224),transforms.ToTensor(),transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])]))
#Getting length of data
num_train = len(train_data)
#Dividing data into train and test loop
indices = list(range(num_train))
np.random.shuffle(indices)
split = int(np.floor(0.5 * num_train))
train_idx, valid_idx = indices[split:], indices[:split]
train_sampler = SubsetRandomSampler(train_idx)
test_sampler = SubsetRandomSampler(valid_idx)
train_loader = torch.utils.data.DataLoader(train_data, batch_size=16,sampler = train_sampler)
test_loader = torch.utils.data.DataLoader(train_data, batch_size=16,sampler = test_sampler)

#Defining model and changing output features
vgg16 = models.vgg16(pretrained=True)
print(vgg16)
vgg16.classifier[6] = nn.Linear(4096,2 )
vgg16.cuda()

#Defining optimizer and loss function
optimizer = optim.SGD(vgg16.classifier.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

#Defining train loop

epochs = 20
max_correct = 0.0
for e in range(epochs):
    train_loss = 0.0
    correct = 0.0
    
    total = 0.0
    for batch_idx, (images, labels) in enumerate(train_loader):
        images = images.cuda()
        labels = labels.cuda()
        output = vgg16(images)
        
        loss = criterion(output,labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        train_loss = train_loss + ((1 / (batch_idx + 1)) * (loss.data - train_loss))
        print(train_loss)
        pred = output.data.max(1, keepdim=True)[1]
        correct += np.sum(np.squeeze(pred.eq(labels.data.view_as(pred))).cpu().numpy())
        total += images.size(0)
    print(e)
    print('\nTrain Accuracy: %2d%% (%2d/%2d)' % (
        100. * correct / total, correct, total))
    if correct > max_correct:
        max_correct = correct
        torch.save(vgg16.state_dict(), 'model_cifar.pt')
        print('Saving Model... ')
        
#Test loop 

# track test loss
vgg16.load_state_dict(torch.load('model_cifar.pt'))
test_loss = 0.0
class_correct = list(0. for i in range(10))
class_total = list(0. for i in range(10))


# iterate over test data
for batch_idx, (images, labels) in enumerate(test_loader):
    # move tensors to GPU if CUDA is available
   
    data, target = images.cuda(), labels.cuda()
    # forward pass: compute predicted outputs by passing inputs to the model
    output = vgg16(data)
    
    # calculate the batch loss
    loss = criterion(output, target)
    # update test loss 
    test_loss += loss.item()*data.size(0)
    # convert output probabilities to predicted class
    pred = output.data.max(1, keepdim=True)[1] 
    # compare predictions to true label
    correct += np.sum(np.squeeze(pred.eq(target.data.view_as(pred))).cpu().numpy())
    total += images.size(0)
    # calculate test accuracy for each object class
print('\nTest Accuracy: %2d%% (%2d/%2d)' % (
        100. * correct / total, correct, total))  
