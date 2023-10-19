import csv

from django.core.management.base import BaseCommand, CommandParser

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузить данные об ингридиентах.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        with open(options['csv_file'], newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                _, created = Ingredient.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1]
                )
