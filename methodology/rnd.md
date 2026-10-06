# R&D method

Normative upstream process: `superpowers:brainstorming` from [obra/superpowers](https://github.com/obra/superpowers).

The R&D stage must:

1. classify the request as `spike`, `bounded`, or `architectural` and announce the chosen path;
2. inspect repository context before asking questions;
3. resolve material product, flow, state, data, integration, and delivery uncertainty;
4. present a design scaled to the classification, including alternatives for architectural work;
5. record explicit human approval before development.

The resulting feature brief records the upstream framework, process, classification, and approval evidence. Missing approval yields `approval_required`; it is not treated as a successful R&D gate. Hidden complexity requires reclassification.

This harness adds mobile-specific state coverage, acceptance criteria, dependency maps, risk register, and scope. Those extend the Superpowers method rather than replacing it.

