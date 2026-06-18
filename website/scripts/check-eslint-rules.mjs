import { ESLint } from "eslint";

const eslint = new ESLint();
const requiredRules = {
  curly: ["error", "all"],
  eqeqeq: ["error", "always"],
  "no-tabs": ["error", { allowIndentationTabs: false }],
  "no-var": "error",
  "prefer-const": [
    "error",
    { destructuring: "all", ignoreReadBeforeAssign: false },
  ],
};

function normalizeRule(rule) {
  if (Array.isArray(rule)) {
    const normalizedRule = rule.map((value) => (value === 2 ? "error" : value));
    return normalizedRule.length === 1 ? normalizedRule[0] : normalizedRule;
  }

  return rule === 2 ? "error" : rule;
}

const config = await eslint.calculateConfigForFile("src/App.tsx");

for (const [ruleName, expected] of Object.entries(requiredRules)) {
  const actual = normalizeRule(config.rules?.[ruleName]);
  const normalizedExpected = normalizeRule(expected);

  if (JSON.stringify(actual) !== JSON.stringify(normalizedExpected)) {
    throw new Error(
      `Expected ESLint rule ${ruleName} to be ${JSON.stringify(
        normalizedExpected
      )}, received ${JSON.stringify(actual)}`
    );
  }
}

const [probe] = await eslint.lintText(
  [
    "export function eslintCurlyProbe(value: boolean) {",
    "  if (value) return 1;",
    "  return 0;",
    "}",
  ].join("\n"),
  { filePath: "src/eslint-curly-probe.ts" }
);

const reportedRuleIds = probe.messages.map((message) => message.ruleId);

if (!reportedRuleIds.includes("curly")) {
  throw new Error(
    `Expected ESLint to report curly for missing braces, received ${reportedRuleIds.join(
      ", "
    )}`
  );
}
