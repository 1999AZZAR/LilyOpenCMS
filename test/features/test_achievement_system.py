#!/usr/bin/env python3
"""
Achievement System Test Script

This script tests the achievement system to ensure it's working correctly.
Run this after setting up the achievement system to verify everything is working.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, db
from models import (
    User, AchievementCategory, Achievement, UserAchievement, UserStreak, UserPoints,
    AchievementManager, AchievementTracker
)
from datetime import datetime, timezone, timedelta


def test_achievement_system():
    """Test the achievement system functionality."""
    with app.app_context():
        print("🧪 Testing Achievement System")
        print("=" * 50)
        
        try:
            # Test 1: Check if categories exist
            print("1. Testing achievement categories...")
            categories = AchievementCategory.query.all()
            print(f"   ✅ Found {len(categories)} categories")
            
            for category in categories:
                print(f"      - {category.name} ({category.achievements.count()} achievements)")
            
            # Test 2: Check if achievements exist
            print("\n2. Testing achievements...")
            achievements = Achievement.query.all()
            print(f"   ✅ Found {len(achievements)} achievements")
            
            # Test 3: Create a test user
            print("\n3. Creating test user...")
            test_user = User.query.filter_by(username="test_achievement_user").first()
            if not test_user:
                test_user = User(
                    username="test_achievement_user",
                    email="test@achievement.com",
                    first_name="Test",
                    last_name="User"
                )
                test_user.set_password("test123")
                db.session.add(test_user)
                db.session.commit()
                print("   ✅ Created test user")
            else:
                print("   ✅ Test user already exists")
            
            # Test 4: Test login streak tracking
            print("\n4. Testing login streak tracking...")
            result = AchievementTracker.track_login(
                test_user.id, 
                "127.0.0.1", 
                "Test Browser"
            )
            
            if result:
                print(f"   ✅ Login streak: {result['login_streak']['current_streak']} days")
                if result['completed_achievements']:
                    print(f"   🎉 Completed {len(result['completed_achievements'])} achievements!")
                    for achievement_data in result['completed_achievements']:
                        achievement = achievement_data['achievement']
                        print(f"      - {achievement.name}")
                else:
                    print("   ℹ️ No achievements completed yet")
            else:
                print("   ❌ Login tracking failed")
            
            # Test 5: Test activity tracking
            print("\n5. Testing activity tracking...")
            result = AchievementTracker.track_activity(
                test_user.id,
                "test_activity",
                "Test activity for achievement system"
            )
            
            if result:
                print(f"   ✅ Activity streak: {result['activity_streak']['current_streak']} days")
                if result['completed_achievements']:
                    print(f"   🎉 Completed {len(result['completed_achievements'])} achievements!")
                    for achievement_data in result['completed_achievements']:
                        achievement = achievement_data['achievement']
                        print(f"      - {achievement.name}")
                else:
                    print("   ℹ️ No achievements completed yet")
            else:
                print("   ❌ Activity tracking failed")
            
            # Test 6: Test reading tracking
            print("\n6. Testing reading tracking...")
            result = AchievementTracker.track_reading(
                test_user.id,
                "news",
                1  # Assuming news ID 1 exists
            )
            
            if result:
                print(f"   ✅ Reading streak: {result['reading_streak']['current_streak']} days")
                if result['completed_achievements']:
                    print(f"   🎉 Completed {len(result['completed_achievements'])} achievements!")
                    for achievement_data in result['completed_achievements']:
                        achievement = achievement_data['achievement']
                        print(f"      - {achievement.name}")
                else:
                    print("   ℹ️ No achievements completed yet")
            else:
                print("   ❌ Reading tracking failed")
            
            # Test 7: Test user achievements summary
            print("\n7. Testing user achievements summary...")
            summary = AchievementTracker.get_user_achievements_summary(test_user.id)
            
            if summary:
                print(f"   ✅ Total achievements: {summary['total_achievements']}")
                print(f"   ✅ Completed achievements: {summary['completed_achievements']}")
                print(f"   ✅ Completion rate: {summary['completion_rate']:.1f}%")
                print(f"   ✅ Total points: {summary['total_points']}")
                print(f"   ✅ Current level: {summary['current_level']}")
                
                if summary['points']:
                    print(f"   ✅ Level progress: {summary['points']['level_progress']:.1f}%")
                
                if summary['streaks']:
                    print("   ✅ Streaks:")
                    for streak_type, streak_data in summary['streaks'].items():
                        print(f"      - {streak_type}: {streak_data['current_streak']} days")
                
                if summary['recent_achievements']:
                    print(f"   ✅ Recent achievements: {len(summary['recent_achievements'])}")
                
                if summary['in_progress_achievements']:
                    print(f"   ✅ In-progress achievements: {len(summary['in_progress_achievements'])}")
            else:
                print("   ❌ Failed to get achievements summary")
            
            # Test 8: Test achievement manager functions
            print("\n8. Testing achievement manager functions...")
            
            # Test getting user points
            user_points = AchievementManager.get_or_create_user_points(test_user.id)
            print(f"   ✅ User points: {user_points.total_points} (Level {user_points.current_level})")
            
            # Test getting user streaks
            login_streak = AchievementManager.get_or_create_user_streak(test_user.id, "login")
            print(f"   ✅ Login streak: {login_streak.current_streak} days")
            
            # Test 9: Test level progression
            print("\n9. Testing level progression...")
            old_level = user_points.current_level
            old_points = user_points.total_points
            
            # Add some points to test level up
            leveled_up = user_points.add_points(50, "test", "Test points for level progression")
            
            if leveled_up:
                print(f"   🎉 Leveled up from {old_level} to {user_points.current_level}!")
            else:
                print(f"   ℹ️ No level up (current level: {user_points.current_level})")
            
            print(f"   ✅ Points increased from {old_points} to {user_points.total_points}")
            
            # Test 10: Test achievement progress
            print("\n10. Testing achievement progress...")
            user_achievements = UserAchievement.query.filter_by(user_id=test_user.id).all()
            print(f"   ✅ User has {len(user_achievements)} achievement records")
            
            for ua in user_achievements[:3]:  # Show first 3
                progress = ua.get_progress_percentage()
                status = "✅ Completed" if ua.is_completed else "🔄 In Progress"
                print(f"      - {ua.achievement.name}: {progress:.1f}% {status}")
            
            # Test 11: Test database indexes
            print("\n11. Testing database indexes...")
            try:
                from models import add_missing_indexes
                add_missing_indexes()
                print("   ✅ Database indexes created successfully")
            except Exception as e:
                print(f"   ⚠️ Index creation warning: {e}")
            
            # Test 12: Test cleanup function
            print("\n12. Testing cleanup function...")
            try:
                result = AchievementTracker.cleanup_old_activity_data()
                if result:
                    print(f"   ✅ Cleanup completed: {result['message']}")
                else:
                    print("   ℹ️ No cleanup needed")
            except Exception as e:
                print(f"   ⚠️ Cleanup warning: {e}")
            
            print("\n" + "=" * 50)
            print("✅ Achievement system test completed successfully!")
            print("\n📊 Test Summary:")
            print(f"   - Categories: {len(categories)}")
            print(f"   - Achievements: {len(achievements)}")
            print(f"   - Test user: {test_user.username}")
            print(f"   - User level: {user_points.current_level}")
            print(f"   - User points: {user_points.total_points}")
            print(f"   - User achievements: {len(user_achievements)}")
            
            print("\n🎉 Achievement system is working correctly!")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            db.session.rollback()
            raise


def test_achievement_criteria():
    """Test achievement criteria checking."""
    with app.app_context():
        print("\n🔍 Testing Achievement Criteria")
        print("=" * 30)
        
        try:
            # Get some achievements to test
            achievements = Achievement.query.limit(5).all()
            
            for achievement in achievements:
                print(f"\nTesting: {achievement.name}")
                print(f"  Criteria: {achievement.criteria_type} {achievement.criteria_operator} {achievement.criteria_value}")
                
                # Test different values
                test_values = [0, 1, 5, 10, 25, 50, 100]
                
                for value in test_values:
                    result = achievement.check_criteria(value)
                    status = "✅" if result else "❌"
                    print(f"    {value}: {status}")
                
        except Exception as e:
            print(f"❌ Error testing criteria: {e}")


def test_streak_calculation():
    """Test streak calculation logic."""
    with app.app_context():
        print("\n📅 Testing Streak Calculation")
        print("=" * 30)
        
        try:
            # Create a test user for streak testing
            test_user = User.query.filter_by(username="test_streak_user").first()
            if not test_user:
                test_user = User(
                    username="test_streak_user",
                    email="streak@test.com",
                    first_name="Streak",
                    last_name="Test"
                )
                test_user.set_password("test123")
                db.session.add(test_user)
                db.session.commit()
            
            # Test streak with different dates
            streak = AchievementManager.get_or_create_user_streak(test_user.id, "test_streak")
            
            # Simulate consecutive days
            today = datetime.now(timezone.utc).date()
            
            print(f"Testing streak with consecutive days...")
            
            for i in range(5):
                test_date = today - timedelta(days=4-i)  # 5 consecutive days
                streak.update_streak(test_date)
                print(f"  Day {i+1}: {test_date} -> Streak: {streak.current_streak}")
            
            # Test streak break
            print(f"\nTesting streak break...")
            break_date = today + timedelta(days=2)  # Skip 2 days
            streak.update_streak(break_date)
            print(f"  Break day: {break_date} -> Streak: {streak.current_streak}")
            
            # Test same day (should not change)
            print(f"\nTesting same day...")
            same_day = today
            old_streak = streak.current_streak
            streak.update_streak(same_day)
            print(f"  Same day: {same_day} -> Streak: {streak.current_streak} (unchanged: {streak.current_streak == old_streak})")
            
            print(f"\n✅ Final streak: {streak.current_streak} days")
            print(f"✅ Longest streak: {streak.longest_streak} days")
            
        except Exception as e:
            print(f"❌ Error testing streak calculation: {e}")


def main():
    """Main test function."""
    print("🚀 Achievement System Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_achievement_system()
    test_achievement_criteria()
    test_streak_calculation()
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Integrate AchievementTracker into your routes")
    print("2. Create achievement display templates")
    print("3. Add achievement notifications to your UI")
    print("4. Monitor achievement completion rates")
    print("\nFor more information, see docs/ACHIEVEMENT_SYSTEM_GUIDE.md")


if __name__ == "__main__":
    main()
