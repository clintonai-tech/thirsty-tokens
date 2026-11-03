import nextJest from "next/jest.js";

const createJestConfig = nextJest({ dir: "./" });

// react-markdown and its unified/micromark dependencies ship ES modules only, so Jest has to
// transform them instead of skipping node_modules.
const ESM_PACKAGES = [
    "react-markdown",
    "remark-.*",
    "rehype-.*",
    "unified",
    "bail",
    "trough",
    "vfile.*",
    "unist-.*",
    "mdast-.*",
    "micromark.*",
    "hast-.*",
    "decode-named-character-reference",
    "character-entities.*",
    "property-information",
    "space-separated-tokens",
    "comma-separated-tokens",
    "trim-lines",
    "devlop",
    "html-url-attributes",
    "estree-util-is-identifier-name",
    "is-plain-obj",
    "ccount",
    "markdown-table",
    "zwitch",
    "longest-streak",
    "stringify-entities",
].join("|");

const config = createJestConfig({
    testEnvironment: "jsdom",
    setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
    moduleNameMapper: { "^@/(.*)$": "<rootDir>/$1" },
});

export default async () => {
    const resolved = await config();
    resolved.transformIgnorePatterns = [`/node_modules/(?!(?:${ESM_PACKAGES})/)`];
    return resolved;
};
