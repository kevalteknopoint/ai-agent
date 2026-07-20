# bmad-wp-to-eds

WordPress theme to AEM Edge Delivery Services block migration.

## When to Use

- "Migrate WordPress to EDS / AEM"
- "Convert a WP block to an EDS block"
- "Recreate a WP component in Edge Delivery"
- "Add a new authorable block to an aem-boilerplate-xwalk project"

## Agent

Load `_bmad/agents/wp-to-eds-migrator.md`

## Steps

1. **Inspect WP** — theme structure, blocks, design tokens, identify static vs dynamic
2. **Inspect EDS** — confirm XWalk authoring, read existing blocks/conventions
3. **Plan** — present inventory + consolidation mapping + risk list
4. **Confirm** — get user approval before coding
5. **Model** — write `_<name>.json` partials per block
6. **Build** — `<name>.js` + `<name>.css` per block
7. **Validate** — lint, authoring preview, empty state testing

## Key Principles

- Consolidate many similar WP blocks into minimal reusable EDS blocks
- Reuse EDS default content (text, title, image, button) and existing blocks
- Vanilla only — no framework, no build step
- XWalk: block is EITHER key-value (`model`) OR container (`filter`) — never both
- All CSS scoped to `.blockname .child`
- Run `npm run build:json` after writing partials — never hand-edit root component-*.json
