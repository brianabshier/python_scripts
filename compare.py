file1_path = input("Enter the path of the first file: ")
file2_path = input("Enter the path of the second file: ")

try:
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        lines_file1 = set(file1.readlines())
        lines_file2 = set(file2.readlines())

    matching_lines = lines_file1.intersection(lines_file2)
    non_matching_lines_file1 = lines_file1 - matching_lines
    non_matching_lines_file2 = lines_file2 - matching_lines

    if matching_lines:
        print("Matching lines:")
        for line in matching_lines:
            print(line.strip())
    else:
        print("No matching lines found.")

    if non_matching_lines_file1:
        print("\nNon-matching lines in the first file:")
        for line in non_matching_lines_file1:
            print(line.strip())

    if non_matching_lines_file2:
        print("\nNon-matching lines in the second file:")
        for line in non_matching_lines_file2:
            print(line.strip())

except FileNotFoundError:
    print("File not found. Please check the file paths.")
