import eslint from '@eslint/js';
import prettier from 'eslint-config-prettier';
import tseslint from 'typescript-eslint';

export default tseslint.config(
    { ignores: ['cdk.out', 'node_modules', 'jest.config.js', '**/*.d.ts'] },
    eslint.configs.recommended,
    ...tseslint.configs.strict,
    prettier,
);
