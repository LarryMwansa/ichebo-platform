# Sub-domain Development

Three questions this raises that need decisions before anything else changes:

join.ichebo.org boundary — Does sceptre.ichebo.org ever see a Level 0a user, or does join.ichebo.org own the full induction journey and hand off a Level 0b participant to sceptre.ichebo.org? My recommendation: join.ichebo.org owns induction start to finish. sceptre.ichebo.org entry requirement is Level 0b minimum — induction complete. Clean handoff, no overlap.

learn.ichebo.org vs /learn/ on sceptre — Two options. Option A: the Learn tile on sceptre.ichebo.org links out to learn.ichebo.org — cross-subdomain navigation, participant leaves one surface and enters another. Option B: sceptre.ichebo.org keeps a lightweight Learn summary view (next lesson, progress) and deep links into learn.ichebo.org for actual lesson content. My recommendation: Option B. The Home tile on sceptre.ichebo.org shows the participant's next lesson and progress — tapping it opens learn.ichebo.org. The dedicated study environment is there. This keeps the Home screen coherent without duplicating the full Learn surface.

identity.ichebo.org and the Profile nav item — Two options. Option A: Profile on sceptre.ichebo.org is a lightweight in-surface view (name, photo, community, current level) with a link to identity.ichebo.org for the full record. Option B: Profile nav item on sceptre.ichebo.org links directly to identity.ichebo.org. My recommendation: Option A for now — identity.ichebo.org is still in design, not built. DOC J's Profile approach remains valid as an interim. When identity.ichebo.org ships, the Profile link upgrades to a cross-subdomain redirect. No DOC J rework needed today.
