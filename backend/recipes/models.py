from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        max_length=254, verbose_name='электронная почта', unique=True
    )
    username = models.CharField(
        max_length=150, verbose_name='имя пользователя', unique=True
    )
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    is_subscribed = models.BooleanField(
        editable=False, verbose_name='Подписки', null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
