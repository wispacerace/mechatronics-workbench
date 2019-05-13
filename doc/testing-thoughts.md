# Testing thoughts
## _Liam Marshall_, 12 May 2019

Testing splits up into a few areas (and strategies for those areas).

* [Unit tests](#unit-tests)
  * [Side-effects and unit testing](#side-effects-and-unit-testing)
  * [Running on real hardware](#running-on-real-hardware)
  * [How does this work with continuous integration?](#how-does-this-work-with-continuous-integration)
* [Integration tests](#integration-tests)
  * [Continuous integration](#continuous-integration)
* [System tests](#system-tests)
  * [Continuous integration?](#continuous-integration-1)

# Unit tests
**Unit tests** test a single unit (surprise) of functionality at a time. For instance, if I have the code
```rust
fn add_numbers(a: i32, b: i32) -> i32 { a + b }
```
then I might write a unit test that looked like
```rust
#[test]
fn test_add_numbers() {
    assert_eq!(add_numbers(2, 2), 4);
}
```

Note how we're just testing basic functionality of a subcomponent? This is what unit tests excel at. However, there's a slight problem.

## Side-effects and unit testing 
What if we want to test something a bit more complicated? How about this:
```rust
fn flip_pin_state() {
    LOGIC_PIN.set_state(!LOGIC_PIN.get_state());
}
```

Now we have a problem. This function is not _pure_: it depends on external state, and, worse, messes with it. There's several ways you can test impure functions.

One common method is _mocking_. Mocking involves creating a "fake" `LOGIC_PIN` with known internal state and fake `get_state` and `set_state` getters/setters. `flip_pin_state()` can be run and the internal state of the fake `LOGIC_PIN` checked.

Mocking sometimes is very complicated (monkeypatching language internals to override, eg, class instantiation with mocked classes), but with sufficiently decoupled code, dependency-injection style (pass required things _into_ functions, instead of globals), it's quite a bit easier. Mocking is definitely harder in compiled languages and usually requires special tools; instead, a demonstration in Python:

```py
class ActualLogicPin:
    # does fancy, actual hardware things

class MockLogicPin:
    def __init__(self):
        self.state = False

    def set_state(self, new_state):
        self.state = new_state

    def get_state(self):
        return self.state

def flip_pin_state(pin):
    pin.set_state(not pin.get_state())

def test_flip_pin_state():
    logic_pin = MockLogicPin()
    flip_pin_state(logic_pin) # note how we're passing in the dependency instead of it being a global
    assert logic_pin.state == True
```

## Running on real hardware
Mocking only works to a point; in the real world, `LOGIC_PIN` is fallible and involves memory/register accesses and previous setup. What if we hadn't actually configured it as an output pin?

Another option is _running unit tests on the target_. In this setting, we'd write (_literally_):
```rust
#[test]
fn test_() {
    // setup
    LOGIC_PIN.set_state(false);

    // do the thing
    flip_pin_state();

    // check the results
    assert_eq!(LOGIC_PIN.get_state(), false);
}
```

This code would be compiled for the target devboard and uploaded; the result of the assertion would be sent back over serial. Note that we're polluting global state, though; you have to be very very careful to not affect tests down the line if you do this sort of thing. Ideally, you'll be clearing out system state before every test begins (that's what the `LOGIC_PIN.set_state(false)` is doing there), but you can forget what `flip_pin_state()` touches pretty easily. Another argument for passing dependencies (in this case, `LOGIC_PIN`) in as arguments!

## How does this work with continuous integration?
Continuous integration tools like [Travis CI](https://travis-ci.org/) watch your Git repository for changes and run your tests on every new commit; this has become increasingly integrated to the point that Github supports displaying test status on pull requests and preventing merges without tests passing.

We want to at least run the build and make sure everything compiles, but in addition to that, there's some other possibilities:
* Run unit tests on pure functions/suitably decoupled portions of the codebase.
* Run unit tests with mocked hardware.
* Run unit tests on physical hardware.

Cooperating with physical hardware requires that tests run on the workbench machine, which (somewhat) rules out Travis. This is something I'll have to research.

# Integration tests
Integration tests attempt to validate modules and subsystems within the context they operate in. For example, ECU functionality would be tested by sending CAN commands and making sure the right outputs were asserted. Integration testing can be (somewhat) performed by mocking hardware but ideally would be performed physically, to make sure that subsystems communicate properly. For consistency, it's pretty common to replace some of the subsystems with accurate mocks so that it's possible to isolate issues to the unit under test.

## Continuous integration
* Run integration tests on subsets of the codebase with mocked hardware.
* Run integration tests on physical hardware (needs CAN injector/debugger hardware, testbenched I/O).

# System tests
System tests are run on rocket mechatronics with all subsystems active and networked (ECU, FCU, sensors, telemetry, etc). I/O will be checked/asserted in real time and CAN will be monitored. This is almost validation testing, just with more automation; due to the level of integration and the required runtime, these will be run with lower frequency than hardware unit or integration tests.

## Continuous integration?
Not really. Tests would still be automated, though. Hardware setup would look a lot like continuous integration, just testing everything at once; for instance, the ECU and FCU would actually be talking as in the full rocket system, whereas ECU integration tests would pretend to be sending FCU commands.