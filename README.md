# CS 517 Final Project

I take my model that I use in my research based around Game Theory and perform a reduction from an SMT. 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

First:

```
Have Python 3.7
```
I used the PySMT library along with the copy library, which should be available in all distributions. In case it's not, here is how you can install it:

```
pip3 install pysmt
pip3 install copy
```

### Installing

Just run the code provided and watch it do the rest!!!

```
python3 solver.py
```

## Different Settings

I have commented out many different settings that you can use, but here are some test cases.


### From Paper 
```
intents = ['CS', 'EE']
queries = ['x', 'y']
tuples = ['CS517', 'EE433']
matches = [('CS', 'CS517'), ('EE', 'EE433')]
```

### Basic 2 intents 

```
intents = ['apple', 'orange']
queries = ['x', 'y']
tuples = ['apple gross', 'orange tasty']
matches = [('apple', 'apple gross'), ('orange', 'orange tasty')]
```

### Basic 3 intents

```
intents = ['apple', 'orange', 'plum']
queries = ['x', 'y', 'z']
tuples = ['apple gross', 'orange tasty', 'plum oh boy!']
matches = [('apple', 'apple gross'), ('orange', 'orange tasty'), ('plum', 'plum oh boy!')]
```

### Not enough signals

```
intents = ['apple', 'orange', 'plum']
queries = ['a', 'x']
tuples = ['apple gross', 'orange tasty', 'plum oh boy!']
matches = [('apple', 'apple gross'), ('orange', 'orange tasty'), ('plum', 'plum oh boy!')]
```
### More than one correct answer

```
intents = ['apple', 'orange']
queries = ['a', 'x']
tuples = ['apple gross', 'orange tasty', 'apple oh boy!']
matches = [('apple', 'apple gross'), ('orange', 'orange tasty'), ('apple', 'apple oh boy!')]
```

### Too many possible answers

```
intents = ['apple', 'orange']
queries = ['a', 'x']
tuples = ['apple gross', 'orange tasty', 'plum oh boy!']
matches = [('apple', 'apple gross'), ('orange', 'orange tasty'), ('plum', 'plum oh boy!')]
```

### I am feeling crazy mode

```
intents = ['1', '2', '3', '4', '5', '6', '7', '8', '9','10']
queries = ['x', 'y', 'z', 'a', 'b']
tuples = ['1', '2', '3', '4', '5', '6', '7', '8', '9','10']
matches = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')]
```

## Settings to call
The parameters with descriptions are in the comments of the code.

### Test Nash

```
findNashEquilibria(intents, queries, tuples, matches, False, False, 1)
```

### Test Strict Nash (May not find solution)

```
findNashEquilibria(intents, queries, tuples, matches, True, False, 1)
```

### Test Minimum Reward of 1 (May not find solution)
```
findNashEquilibria(intents, queries, tuples, matches, False, True, 1)
```

## Authors

* **Ben MCCamish** - *All work*

## License

This project is licensed under the CRAPL License - see the [CRAPL-LICENSE.txt](CRAPL-LICENSE.txt) file for details

## Acknowledgments

* Brent Carmer for helping me with some funky PySMT problems... didn't figure them out but hey
* Mike Rosulek for putting up with my constant office visits
* Inspiration
