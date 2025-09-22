# README for LLM README Generator

## Project Overview

The LLM README Generator is a powerful tool designed to automate the generation of README files for software repositories using Large Language Models (LLMs) like DeepSeek. This project aims to streamline the documentation process, enabling developers to focus on coding while ensuring their projects have comprehensive documentation readily available. 

## Installation Instructions

To install the necessary dependencies, ensure you have Python (version 3.6 or later) installed on your system. You can use the provided `pyproject.toml` file to install dependencies. Run the following command in your terminal:

```bash
pip install .
```

This command will install the package and its dependencies.

## Usage Guide

After the installation, you can start using the LLM README Generator. The main entry point is the `cli.py` file, which provides a command-line interface for generating README files. 

Here's an example command to generate a README:

```bash
python src/llm_readme_gen/cli.py --dir /path/to/your/repository
```

Replace `/path/to/your/repository` with the path to the repository for which you want to generate the README.

### Additional Usage

1. **Analyzing Repository**:
   You can use the analyzer script directly to analyze specific aspects of your repository:

   ```bash
   python src/llm_readme_gen/analyzer.py --dir /path/to/your/repository
   ```

2. **Building README**:
   If you want to manually build a README file using the builder, you can specify the repository directory as follows:

   ```bash
   python src/llm_readme_gen/builder.py --dir /path/to/your/repository
   ```

## Project Structure

The project has the following structure:

```
.
├── .git
│   ├── hooks
│   │   ├── pre-commit.sample
│   │   ├── pre-rebase.sample
│   │   ├── fsmonitor-watchman.sample
│   │   └── update.sample
│   └── objects
│       └── pack
│           └── pack-539b00c8499b2afb956c4d5fd17abbf8935dba13.pack
├── .DS_Store
└── src
    └── llm_readme_gen
        ├── builder.py
        ├── analyzer.py
        ├── llm_client.py
        └── cli.py
```

## Testing Instructions

The project includes unit tests to ensure functionality. You can run the tests using the following command:

```bash
pytest
```

Make sure you have `pytest` installed in your Python environment. If not, you can install it using:

```bash
pip install pytest
```

## License Information

This project is licensed under the terms specified in the LICENSE file. Please refer to this file for more information on usage and distribution rights.

---

For more detailed information about the features and capabilities of the LLM README Generator, please visit the [GitHub repository](https://github.com/sinatav/llm-readme-gen.git).