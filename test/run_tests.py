#!/usr/bin/env python3
"""
Comprehensive Test Runner Script
Executes all tests, cleans up test data, and generates CSV reports
"""

import os
import sys
import subprocess
import time
import csv
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRunner:
    """Comprehensive test runner with reporting"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.test_files = []
        self.report_dir = Path("test/reports")
        self.report_dir.mkdir(exist_ok=True)
        
    def discover_tests(self):
        """Discover all test files in the test directory"""
        print("🔍 Discovering test files...")
        
        test_dir = Path("test")
        for file in test_dir.glob("test_*.py"):
            if file.name != "run_tests.py":
                self.test_files.append(file)
        
        print(f"✅ Found {len(self.test_files)} test files:")
        for file in self.test_files:
            print(f"  - {file.name}")
        
        return self.test_files
    
    def run_single_test(self, test_file):
        """Run a single test file and capture results"""
        print(f"\n🧪 Running {test_file.name}...")
        
        start_time = time.time()
        
        try:
            # Run the test file
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse the output for success/failure indicators
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            # Look for specific success/failure patterns
            if "✅ ALL TESTS PASSED" in output or "✅ All tests completed" in output:
                success = True
            elif "❌ SOME TESTS FAILED" in output or "❌ Error" in output:
                success = False
            
            # Count test cases
            test_cases = output.count("✅ Success:") + output.count("❌ Failed:") + output.count("❌ Error:")
            
            test_result = {
                'file': test_file.name,
                'success': success,
                'duration': round(duration, 2),
                'return_code': result.returncode,
                'test_cases': test_cases,
                'output': output,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                print(f"✅ {test_file.name} completed successfully ({duration:.2f}s)")
            else:
                print(f"❌ {test_file.name} failed ({duration:.2f}s)")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file.name} timed out")
            return {
                'file': test_file.name,
                'success': False,
                'duration': 300,
                'return_code': -1,
                'test_cases': 0,
                'output': "Test timed out after 5 minutes",
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"💥 {test_file.name} crashed: {e}")
            return {
                'file': test_file.name,
                'success': False,
                'duration': 0,
                'return_code': -1,
                'test_cases': 0,
                'output': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_all_tests(self):
        """Run all discovered tests"""
        print("🚀 Starting comprehensive test run...")
        print("=" * 60)
        
        self.discover_tests()
        
        for test_file in self.test_files:
            result = self.run_single_test(test_file)
            self.test_results.append(result)
        
        print("\n" + "=" * 60)
        print("📊 Test Run Summary")
        print("=" * 60)
    
    def cleanup_test_data(self):
        """Clean up test data from database and files"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Import cleanup functions
            from test.test_subscription_system import cleanup_test_data as cleanup_subscriptions
            from test.test_database_models import cleanup_test_data as cleanup_models
            
            # Clean up subscription test data
            try:
                cleanup_subscriptions()
                print("  ✅ Subscription test data cleaned")
            except Exception as e:
                print(f"  ⚠️ Subscription cleanup failed: {e}")
            
            # Clean up model test data
            try:
                cleanup_models()
                print("  ✅ Model test data cleaned")
            except Exception as e:
                print(f"  ⚠️ Model cleanup failed: {e}")
            
            # Clean up temporary files
            temp_files = [
                "test_*.jpg",
                "test_*.png", 
                "test_*.gif",
                "temp_*.txt",
                "test_*.json"
            ]
            
            for pattern in temp_files:
                for file in Path(".").glob(pattern):
                    try:
                        file.unlink()
                        print(f"  ✅ Removed temporary file: {file}")
                    except Exception:
                        pass
            
            print("  ✅ Test data cleanup completed")
            
        except Exception as e:
            print(f"  ❌ Cleanup failed: {e}")
    
    def generate_csv_report(self):
        """Generate CSV report with test results"""
        print("\n📊 Generating CSV report...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.report_dir / f"test_report_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Test File',
                'Status',
                'Duration (s)',
                'Test Cases',
                'Return Code',
                'Timestamp',
                'Notes'
            ])
            
            # Write test results
            for result in self.test_results:
                status = "PASS" if result['success'] else "FAIL"
                notes = "Completed successfully" if result['success'] else "Failed or timed out"
                
                writer.writerow([
                    result['file'],
                    status,
                    result['duration'],
                    result['test_cases'],
                    result['return_code'],
                    result['timestamp'],
                    notes
                ])
        
        print(f"  ✅ CSV report saved: {csv_file}")
        return csv_file
    
    def generate_json_report(self):
        """Generate detailed JSON report"""
        print("📊 Generating JSON report...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = self.report_dir / f"test_report_{timestamp}.json"
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        total_duration = sum(r['duration'] for r in self.test_results)
        total_test_cases = sum(r['test_cases'] for r in self.test_results)
        
        report_data = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0,
                'total_duration': round(total_duration, 2),
                'total_test_cases': total_test_cases,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat()
            },
            'test_results': self.test_results
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ JSON report saved: {json_file}")
        return json_file
    
    def print_summary(self):
        """Print test run summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        total_duration = sum(r['duration'] for r in self.test_results)
        total_test_cases = sum(r['test_cases'] for r in self.test_results)
        
        print("\n" + "=" * 60)
        print("📈 TEST RUN SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%" if total_tests > 0 else "0%")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Total Test Cases: {total_test_cases}")
        print(f"Average Duration: {total_duration / total_tests:.2f}s" if total_tests > 0 else "0s")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['file']}: {result['output'][:100]}...")
        
        print("\n" + "=" * 60)
    
    def run(self):
        """Main test runner method"""
        print("🚀 LilyOpenCMS Test Suite Runner")
        print("=" * 60)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # Run all tests
            self.run_all_tests()
            
            # Clean up test data
            self.cleanup_test_data()
            
            # Generate reports
            csv_file = self.generate_csv_report()
            json_file = self.generate_json_report()
            
            # Print summary
            self.print_summary()
            
            print(f"\n📁 Reports saved to: {self.report_dir}")
            print(f"📊 CSV Report: {csv_file}")
            print(f"📊 JSON Report: {json_file}")
            
            # Return success if all tests passed
            all_passed = all(r['success'] for r in self.test_results)
            return 0 if all_passed else 1
            
        except KeyboardInterrupt:
            print("\n⏹️ Test run interrupted by user")
            return 1
        except Exception as e:
            print(f"\n💥 Test runner failed: {e}")
            return 1

def main():
    """Main entry point"""
    runner = TestRunner()
    exit_code = runner.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 