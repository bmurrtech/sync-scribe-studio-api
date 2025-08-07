module.exports = {
  // Formatting rules
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: true,
  quoteProps: 'as-needed',
  trailingComma: 'none',
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: 'avoid',
  endOfLine: 'lf',
  
  // Override for specific files
  overrides: [
    {
      files: '*.json',
      options: {
        printWidth: 200,
        tabWidth: 2
      }
    },
    {
      files: '*.md',
      options: {
        printWidth: 80,
        proseWrap: 'preserve'
      }
    },
    {
      files: ['*.yml', '*.yaml'],
      options: {
        printWidth: 80,
        tabWidth: 2
      }
    }
  ]
};
