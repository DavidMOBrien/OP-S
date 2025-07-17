#!/usr/bin/env python3

print("Starting test...")

try:
    import main
    print("Main module imported successfully")
    
    # Test if main function exists
    if hasattr(main, 'main'):
        print("main() function found")
    else:
        print("main() function NOT found")
    
    # Test if argument parser exists
    if hasattr(main, 'create_argument_parser'):
        print("create_argument_parser() function found")
        parser = main.create_argument_parser()
        print("Argument parser created successfully")
    else:
        print("create_argument_parser() function NOT found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")