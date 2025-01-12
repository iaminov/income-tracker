"""Command-line interface for income tracker."""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from .config import EMAIL_ADDRESS, EMAIL_PASSWORD, EXCEL_FILE_PATH, CHECK_INTERVAL
from .core import IncomeTracker


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("income_tracker.log")
        ]
    )


def validate_environment() -> dict[str, str]:
    """Validate required environment variables.
    
    Returns:
        Dictionary of validated environment variables
        
    Raises:
        SystemExit: If required variables are missing
    """
    missing_vars = []
    
    if not EMAIL_ADDRESS:
        missing_vars.append("EMAIL_ADDRESS")
    if not EMAIL_PASSWORD:
        missing_vars.append("EMAIL_PASSWORD")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        
        print("\nPlease set these environment variables or create a .env file:")
        print("   EMAIL_ADDRESS=your_email@gmail.com")
        print("   EMAIL_PASSWORD=your_app_password")
        print("\nSee .env.example for a complete template.")
        sys.exit(1)
    
    return {
        "email_address": EMAIL_ADDRESS,
        "email_password": EMAIL_PASSWORD,
        "excel_file_path": EXCEL_FILE_PATH,
        "check_interval": CHECK_INTERVAL
    }


def create_tracker(config: dict[str, str]) -> IncomeTracker:
    """Create and validate income tracker instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured IncomeTracker instance
    """
    tracker = IncomeTracker(
        email_address=config["email_address"],
        email_password=config["email_password"],
        excel_file_path=config["excel_file_path"],
        check_interval=int(config["check_interval"])
    )
    
    print("🔍 Validating configuration...")
    validation_results = tracker.validate_configuration()
    
    for component, is_valid in validation_results.items():
        status = "✅" if is_valid else "❌"
        print(f"   {status} {component.replace('_', ' ').title()}")
    
    if not all(validation_results.values()):
        print("\n❌ Configuration validation failed. Please check your settings.")
        sys.exit(1)
    
    print("✅ Configuration validated successfully!")
    return tracker


def cmd_monitor(args: argparse.Namespace) -> None:
    """Run continuous monitoring command.
    
    Args:
        args: Parsed command line arguments
    """
    config = validate_environment()
    tracker = create_tracker(config)
    
    print(f"\n📧 Email: {config['email_address']}")
    print(f"📊 Excel file: {config['excel_file_path']}")
    print(f"⏰ Check interval: {config['check_interval']} seconds")
    print("\n🚀 Starting continuous monitoring...")
    print("   Press Ctrl+C to stop\n")
    
    try:
        tracker.run_continuous_monitoring()
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
        sys.exit(1)


def cmd_check(args: argparse.Namespace) -> None:
    """Run single check command.
    
    Args:
        args: Parsed command line arguments
    """
    config = validate_environment()
    tracker = create_tracker(config)
    
    print("\n🔍 Running single email check...")
    result = tracker.run_single_check()
    
    if "error" in result:
        print(f"❌ Check failed: {result['error']}")
        sys.exit(1)
    
    print(f"✅ Check completed in {result['duration_seconds']}s")
    print(f"   📩 New records processed: {result['records_processed']}")
    print(f"   📨 Total emails processed: {result['total_emails_processed']}")


def cmd_stats(args: argparse.Namespace) -> None:
    """Show statistics command.
    
    Args:
        args: Parsed command line arguments
    """
    config = validate_environment()
    tracker = create_tracker(config)
    
    print("\n📊 Income Tracking Statistics")
    print("=" * 40)
    
    stats = tracker.get_statistics()
    
    if "error" in stats:
        print(f"❌ Error getting statistics: {stats['error']}")
        return
    
    # Storage statistics
    storage = stats.get("storage", {})
    print(f"📁 Total Records: {storage.get('total_records', 0)}")
    print(f"💰 Total Amount: ${storage.get('total_amount', 0):.2f}")
    
    if storage.get('total_records', 0) > 0:
        print(f"📈 Average Payment: ${storage.get('average_amount', 0):.2f}")
        print(f"🔺 Highest Payment: ${storage.get('max_amount', 0):.2f}")
        print(f"🔻 Lowest Payment: ${storage.get('min_amount', 0):.2f}")
        print(f"👥 Unique Clients: {storage.get('unique_clients', 0)}")
        
        # Payment sources breakdown
        by_source = storage.get('by_source', {})
        if by_source:
            print("\n💳 By Payment Source:")
            for source, count in by_source.items():
                print(f"   {source}: {count} payments")
    
    # Monitoring statistics
    monitoring = stats.get("monitoring", {})
    print(f"\n📨 Emails Processed: {monitoring.get('emails_processed', 0)}")
    print(f"🔄 Check Interval: {monitoring.get('check_interval_seconds', 0)}s")
    print(f"📡 Payment Sources: {monitoring.get('supported_payment_sources', 0)}")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate configuration command.
    
    Args:
        args: Parsed command line arguments
    """
    config = validate_environment()
    tracker = create_tracker(config)
    
    print("\n✅ All validations passed!")
    print("   Your income tracker is ready to use.")
    print(f"\n📋 Configuration Summary:")
    print(f"   📧 Email: {config['email_address']}")
    print(f"   📊 Excel file: {config['excel_file_path']}")
    print(f"   ⏰ Check interval: {config['check_interval']}s")
    
    # Show supported payment sources
    supported_senders = tracker.payment_processor.get_supported_senders()
    print(f"\n💳 Monitoring {len(supported_senders)} payment sources:")
    for sender in supported_senders:
        print(f"   • {sender}")


def main() -> None:
    """Main CLI entry point."""
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Advanced income tracking system for freelancers and small businesses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  income-tracker monitor              Start continuous monitoring
  income-tracker check                Run single email check
  income-tracker stats                Show payment statistics
  income-tracker validate             Validate configuration
  
Environment Variables:
  EMAIL_ADDRESS      Gmail address for monitoring
  EMAIL_PASSWORD     Gmail app password
  EXCEL_FILE_PATH    Path to Excel output file (optional)
  CHECK_INTERVAL     Check interval in seconds (optional)
        """
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start continuous email monitoring")
    monitor_parser.set_defaults(func=cmd_monitor)
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Run single email check")
    check_parser.set_defaults(func=cmd_check)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show payment statistics")
    stats_parser.set_defaults(func=cmd_stats)
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.set_defaults(func=cmd_validate)
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    try:
        args.func(args)
    except Exception as e:
        logging.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
