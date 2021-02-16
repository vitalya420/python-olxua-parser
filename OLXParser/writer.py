import csv


class CSVWriter:
    def __init__(self, filename):
        self.filename = filename

    def write(self, data):
        with open(self.filename, "a", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow((str(data[key]) for key in data))
