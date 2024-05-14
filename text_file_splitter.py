def split_file(input_file, lines_per_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    total_lines = len(lines)
    num_files = (total_lines + lines_per_file - 1) // lines_per_file  # Ceiling division

    for i in range(num_files):
        start_idx = i * lines_per_file
        end_idx = min((i + 1) * lines_per_file, total_lines)
        output_file = f"{input_file}_{i + 1}.txt"

        with open(output_file, 'w') as f:
            f.writelines(lines[start_idx:end_idx])

if __name__ == "__main__":
    input_file = input("Enter the path to the input text file: ")
    lines_per_file = int(input("Enter the number of lines per file: "))

    split_file(input_file, lines_per_file)
    print("File split completed.")

