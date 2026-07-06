import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default [
  // Ignore patterns
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'build/**',
      '.next/**',
      '.cache/**',
      'coverage/**',
      '**/*.min.js',
      '**/vendor/**',
    ],
  },

  // JavaScript baseline
  {
    files: ['**/*.js', '**/*.jsx'],
    languageOptions: {
      sourceType: 'module',
      ecmaVersion: 'latest',
      globals: {
        // AEM-specific globals
        Granite: 'readonly',
        CQ: 'readonly',
        $: 'readonly',
        jQuery: 'readonly',
        console: 'readonly',
        window: 'readonly',
        document: 'readonly',
        // Standard browser
        fetch: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        XMLHttpRequest: 'readonly',
      },
    },
    rules: {
      // Best practices
      'curly': ['error', 'all'],
      'eqeqeq': ['error', 'always'],
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      'no-with': 'error',
      'prefer-const': 'warn',
      'no-var': 'warn',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-cond-assign': 'error',
      'no-console': 'warn',

      // Style
      'indent': ['warn', 2],
      'quotes': ['warn', 'single', { avoidEscape: true }],
      'semi': ['warn', 'always'],
      'comma-dangle': ['warn', 'always-multiline'],
      'no-multi-spaces': 'warn',
      'key-spacing': ['warn', { beforeColon: false, afterColon: true }],
      'keyword-spacing': 'warn',
      'space-before-function-paren': ['warn', { anonymous: 'always', named: 'never', asyncArrow: 'always' }],
      'func-style': ['warn', 'declaration', { allowArrowFunctions: true }],
      'max-len': ['warn', { code: 120, ignorePattern: '^\\s*// ', ignoreUrls: true }],
    },
  },

  // TypeScript
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tseslint.parser,
      sourceType: 'module',
      ecmaVersion: 'latest',
      globals: {
        // AEM-specific globals
        Granite: 'readonly',
        CQ: 'readonly',
        $: 'readonly',
        jQuery: 'readonly',
        console: 'readonly',
        window: 'readonly',
        document: 'readonly',
        fetch: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        XMLHttpRequest: 'readonly',
      },
      parserOptions: {
        project: true,
        tsconfigRootDir: process.cwd(),
      },
    },
    rules: {
      // TypeScript rules
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/explicit-function-return-types': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-non-null-assertion': 'warn',
      '@typescript-eslint/no-empty-interface': 'warn',
      '@typescript-eslint/prefer-interface': 'off',
      '@typescript-eslint/no-namespace': 'warn',

      // Shared with JS
      'curly': ['error', 'all'],
      'eqeqeq': ['error', 'always'],
      'no-eval': 'error',
      'prefer-const': 'warn',
      'no-var': 'warn',
      'no-console': 'warn',

      // Style
      'indent': ['warn', 2],
      'quotes': ['warn', 'single', { avoidEscape: true }],
      'semi': ['warn', 'always'],
      'max-len': ['warn', { code: 120, ignorePattern: '^\\s*// ', ignoreUrls: true }],
      'func-style': ['warn', 'declaration', { allowArrowFunctions: true }],
    },
  },
];
