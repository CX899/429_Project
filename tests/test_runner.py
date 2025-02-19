import unittest

if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir="tests", pattern="test_*.py")
    test_runner = unittest.TextTestRunner(verbosity=2)

    # Run the test suite and store the result
    result = test_runner.run(test_suite)

    # Calculate totals
    total_tests = result.testsRun
    total_failures = len(result.failures) + len(result.errors)
    total_passed = total_tests - total_failures

    # Print summary
    print("\n========== Test Summary ==========")
    print(f"Total Tests   : {total_tests}")
    print(f"Total Passed  : {total_passed}")
    print(f"Total Failed  : {total_failures}")
    print("==================================\n")

    # Exit with a nonzero status code if there are failures
    if total_failures > 0:
        exit(1)
