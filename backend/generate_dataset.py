# -*- coding: utf-8 -*-
"""Zgodnościowa uruchamiarka generatora zbioru dla zadania 6."""

from pathlib import Path

from zadania.zadanie_6_SiecNeuronowa.siec import generate_balanced_dataset


def collect_data(required_per_class: int = 1000):
    output_path = Path(__file__).resolve().with_name("rover_training_data.csv")
    dataset = generate_balanced_dataset(required_per_class, output_path=output_path)
    print("Zbieranie danych zakończone. Rozkład klas:")
    print(dataset["target_decision"].value_counts().to_dict())
    return dataset


if __name__ == "__main__":
    collect_data()
