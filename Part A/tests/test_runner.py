import unittest
import sys
from termcolor import colored
from datetime import datetime

class DetailedTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.successes = []
        self.start_time = None
        self.end_time = None

    def startTest(self, test):
        self.start_time = datetime.now()
        super().startTest(test)

    def addSuccess(self, test):
        self.end_time = datetime.now()
        self.successes.append((test, self.end_time - self.start_time))
        super().addSuccess(test)

class DetailedTestRunner(unittest.TextTestRunner):
    resultclass = DetailedTestResult

def run_tests():
    # Configure test discovery
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir="tests", pattern="test_*.py")

    # Create and run the test runner
    runner = DetailedTestRunner(verbosity=2)
    print(colored("\n=== Starting Test Suite Execution ===", "cyan"))
    result = runner.run(test_suite)

    # Calculate timing
    total_time = sum((duration.total_seconds() for _, duration in result.successes), 0)

    # Print detailed summary
    print("\n" + colored("========== Detailed Test Summary ==========", "cyan"))

    # Print successful tests
    if result.successes:
        print(colored("\nPassed Tests:", "green"))
        for test, duration in result.successes:
            print(f"✓ {test} ({duration.total_seconds():.3f}s)")

    # Print failed tests
    if result.failures:
        print(colored("\nFailed Tests:", "red"))
        for test, error in result.failures:
            print(f"✗ {test}")
            print(colored(f"  Error: {error}", "red"))

    # Print errors
    if result.errors:
        print(colored("\nErrors:", "red"))
        for test, error in result.errors:
            print(f"⚠ {test}")
            print(colored(f"  Error: {error}", "red"))

    # Calculate totals
    total_tests = result.testsRun
    total_failures = len(result.failures) + len(result.errors)
    total_passed = total_tests - total_failures

    # Print summary statistics
    print(colored("\n========== Test Statistics ==========", "cyan"))
    print(f"Total Tests    : {colored(total_tests, 'cyan')}")
    print(f"Passed Tests   : {colored(total_passed, 'green')}")
    print(f"Failed Tests   : {colored(total_failures, 'red')}")
    print(f"Success Rate   : {colored(f'{(total_passed/total_tests)*100:.1f}%', 'cyan')}")
    print(f"Total Duration : {colored(f'{total_time:.2f}s', 'cyan')}")
    print(colored("===================================", "cyan"))

    # Print final status
    if total_failures == 0:
        print(colored("\n✅ All tests passed successfully!", "green"))
    else:
        print(colored(f"\n❌ {total_failures} tests failed!", "red"))

    return total_failures

if __name__ == "__main__":
    # Install termcolor if not present
    try:
        from termcolor import colored
    except ImportError:
        print("Installing required package: termcolor")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "termcolor"])
        from termcolor import colored

    # Run tests and exit with appropriate code
    exit_code = run_tests()
    sys.exit(exit_code)
