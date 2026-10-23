# Braitenberg Vehicle 7: Associative Learning Simulation

## Overview

This project implements a Python simulation inspired by Braitenberg Vehicle 7, demonstrating how simple learning mechanisms can change an autonomous agent's behavior.

The vehicle responds to red and blue light stimuli using sensors, threshold devices, and adaptive connections. Through associative learning, a stimulus that was initially neutral can become associated with danger.

## Features

- **Light sensing:** Detects red and blue light sources using left and right sensors.
- **Threshold devices:** Process sensor signals and generate behavioral outputs.
- **Associative learning:** Learns associations between danger-related and neutral stimuli.
- **Hebbian learning:** Strengthens connections when connected devices are simultaneously active.
- **Adaptive connection weights:** Models learned associations using connection strengths that increase or decay over time.
- **Motor control:** Converts sensor and learning signals into vehicle movement and steering.
- **Real-time simulation:** Visualizes how the vehicle's behavior changes as it learns.

## How It Works

1. The vehicle detects red and blue light through its sensors.
2. Red light activates the danger-related response, while blue light initially acts as a neutral stimulus.
3. When the relevant danger and neutral signals are active together, the connection weight increases.
4. The learned connection allows blue light to influence the danger response.
5. The vehicle's motor speeds and movement change according to its sensor inputs and learned connections.

## Technologies

- Python
- Pygame (for visualization, if used in the implementation)
- Object-oriented programming
- Associative learning and Hebbian learning concepts

## Learning Concepts Demonstrated

- Autonomous agent behavior
- Sensor-driven control
- Threshold-based processing
- Hebbian learning
- Associative memory
- Adaptive connection weights

## Getting Started

### Prerequisites

- Python 3
- Pygame

### Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/braitenberg-vehicle-7-associative-learning.git
cd braitenberg-vehicle-7-associative-learning
```

Install the dependency if the project uses Pygame:

```bash
python -m pip install pygame
```

### Run the Simulation



```bash
python vehicle7_base.py
```


## Future Improvements

- Add visualizations of learning-weight changes.
- Compare vehicle behavior before and after learning.
- Add configurable learning and decay rates.
- Record simulation results for different training conditions.
- Add automated tests for the learning mechanisms.

## Purpose

This project explores how relatively simple neural-inspired mechanisms can produce adaptive behavior in an autonomous agent.
