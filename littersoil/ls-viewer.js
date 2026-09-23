/* LitterSoil action-plan viewer.
   Three.js comes from the shared Meadowlark loader (local /insect/vendor, then CDN).
   Copy is the locked plan: Path A Cascade, purchase HOLD, Track 2 not a soil score.
*/
(function () {
  'use strict';

  var ITEMS = {
    bags: {
      chip: 'Bags',
      name: 'Bagged unsorted trash',
      tags: ['plan', 'speculative'],
      summary: 'Most household trash shows up in a bag: food, paper, cardboard, and a mix of plastic, glass, and metal. LitterSoil keeps that unsorted bag as the real starting point. Biology can work on the food and paper once the bag is open. It does not, on current evidence, turn the plastic, glass, and metal into soil.',
      deeper: [
        'The operating story is landfill-easy in: no hand-sorting and no hand de-bagging at the pile. Occasional mixing is allowed.',
        'Near-term success is still the organic fraction becoming a mature amendment, plus a screen so physical junk does not ride along to land.',
        'Calling the whole bag “soil” would be a false claim. The bag is the ambition. The scoreboard is narrower.',
        'Messier personal bags are a later dress rehearsal, after a candidate crew exists. They do not replace the clean base recipes.'
      ]
    },
    crush: {
      chip: 'Crush / shred',
      name: 'Crush / shred',
      tags: ['proven', 'plan'],
      summary: 'Crushing or shredding is the allowed front step. It pops bags and exposes food and paper so the crew can reach them. It does not teach plastic to biodegrade. It only stops organics from staying trapped in plastic film.',
      deeper: [
        'Every comparison pile gets the same crush, including the twin with no added microbes, so a win can be credited to biology rather than to shredding.',
        'Mobile shredder versus a pad shredder, and the target particle size, are still open equipment choices.',
        'Plastics, glass, and metal coming out of the crusher are contaminants for a land-apply grade unless the separate research track someday earns a different claim.',
        'Purchase HOLD covers the machine too. This view is not a buy list.'
      ]
    },
    zero: {
      chip: 'Crush-only twin',
      name: 'Crush-only twin',
      tags: ['plan'],
      summary: 'One twin gets the same crushed feedstock, the same water, and the same turning, and no added microbes. It exists so a faster pile can be credited to the inoculum rather than to the shredder. Path A has to beat this twin and the native-compost twin.',
      deeper: [
        'Matched care: if you remoisten or turn the inoculated bins, the zero bins get the same treatment. No rescue-only watering.',
        'If nothing beats crush-only plus native compost, the specialty packs are not earning their keep.',
        'Plastic pieces getting smaller do not count as this twin losing. Track 1 scores organic loss and plant-safe finish only.'
      ]
    },
    room: {
      chip: 'Air, water, C/N',
      name: 'Moisture, air, and carbon-to-nitrogen',
      tags: ['proven'],
      summary: 'The pile fails if the room is wrong. Moisture should feel like a wrung-out sponge: the plan’s band is 50–60% water after the inoculum water goes in. Without air, the pile turns sour. Paper is extremely carbon-heavy and food brings nitrogen, so the blend has to meet in the middle.',
      deeper: [
        'Starting carbon-to-nitrogen (C/N) on the mixed recipe is aimed at about 25–40, with ~30 as the working target. The finish band is a different, tighter range near 10–20.',
        'Too wet means stink and sour acids. Too dry and the biology stalls. Fix air and water before adding more microbes.',
        'A sour pile that stays airless for more than about 72 hours after an aeration fix is a process failure. Do not blame the crew first.',
        'These conditions are ordinary compost practice. They are not a special organism.'
      ]
    },
    pathA: {
      chip: 'Path A',
      name: 'Path A Cascade',
      tags: ['plan', 'hold'],
      summary: 'Wave 1’s default inoculum is Path A Cascade. A staged team of ordinary compost microbes goes in at the start as one dry pack: fast food-and-starch bacteria first in line, then a heat-tolerant fiber crew. This is a role-and-timing plan under purchase hold, not a shopping list of named products.',
      deeper: [
        'Planning dose: the combined dry pack at 0.5% by weight of wet feedstock. That number is a trial freeze, not permission to buy.',
        'Optional Trichoderma in that start pack is capped at 20% of the fiber crew. Wood-rot fungi are not in this field pack.',
        'The team has to beat two twins: shovel-in native compost (Path D) and crush-and-mix with nothing added.',
        'If a mixed team destroys a win that one role had alone, do not average the scores. Change timing or dose and try again.'
      ]
    },
    pathB: {
      chip: 'Path B',
      name: 'Path B Hot-core',
      tags: ['plan', 'hold'],
      summary: 'Path B is the parallel honesty and speed arm, not the default pack. It pushes a hotter bacterial cycle after the crush, using a water-only slurry of the heat-tolerant roles. Heat is a diagnostic. It is not a finished amendment until mature compost fines go in at the cure.',
      deeper: [
        'Planning dose: 1.0% by weight slurry solids. No molasses. No fungi in the slurry. Treat the mix as short-lived, on the order of a few hours.',
        'Finish fines are mandatory after Path B. Hot without a cure is not a soil amendment.',
        'Time above 55°C can be useful later as compost-standard context. It does not replace fiber loss or plant-safety tests. A mini-bin is not a regulatory sanitation claim.',
        'Path B stays in the comparison grid. It does not replace Path A as the Wave 1 default.'
      ]
    },
    pathD: {
      chip: 'Path D',
      name: 'Path D native compost',
      tags: ['plan', 'proven'],
      summary: 'Path D is ordinary mature compost plus the same crush. It is the “nature already does this” control, not an engineered product. Path A only earns its keep if it beats this shovel compost and the crush-only pile.',
      deeper: [
        'Planning dose for the native control is 10% by volume.',
        'Path D is never scored as an engineered win. It is the bar.',
        'A fungal-led path (the plan’s Path C) can be an optional edge after cool-down. It is not the engine for unsorted trash, and it is not this control.'
      ]
    },
    heat: {
      chip: 'Heat / fiber',
      name: 'Heat window and fiber attack',
      tags: ['proven'],
      summary: 'After the easy food carbon is used up, the pile can get hot and the fiber crew works on cardboard and leaves: cellulose and hemicellulose, the scaffolding in paper and plants. Success is the fiber actually losing mass versus a twin that got the same process and no inoculum. A warm thermometer by itself does not count.',
      deeper: [
        'The gate that blocks the Cascade is a paper coupon: the inoculated pile has to clearly beat the matched zero pile before Path A advances.',
        'Dry-out kills this stage. If you remoisten, remoisten the zero twins too.',
        'The cross-section in the view is a schematic: outer pile, a fiber band, a hot core, and a few air pockets. It is not a measured temperature map.',
        'Analogy from the plan: the first crew clears the counter. This crew works the tough dough.'
      ]
    },
    cool: {
      chip: 'Cool-down',
      name: 'Cool-down assist',
      tags: ['plan'],
      summary: 'When the hot core settles below about 40°C, you may optionally add one cool-down assist: either a Trichoderma-class fungus helper, or weathered leftover from oyster-mushroom farming. Never both in one arm. Never wood-rot fungi in the Wave 1 field pack. Fungi tossed into a raging hot core tend to get cooked.',
      deeper: [
        'Which assist to keep — fungus, mushroom leftover, or neither — can wait. It does not block Wave 1 planning.',
        'Run the two assists as separate test series. Do not blend them into one pack.',
        'If a fungal add-on knocks the fiber coupon down by about 30% or more versus the fiber crew alone, that series is dropped.',
        'Do not turn the pile aggressively for a few days after the fungus dose. The mushroom leftover needs a salt check first.'
      ]
    },
    cure: {
      chip: 'Cure',
      name: 'Cure and plant-safe finish',
      tags: ['proven', 'plan'],
      summary: 'The pile has to finish until it is safer for plants. Free ammonia can burn seedlings. Unfinished compost can lock up nitrogen or smell wrong. The finish line is a pair of checks used across compost science: a germination index (GI) of at least 80%, and a carbon-to-nitrogen ratio (C/N) that has settled near 10–20. Calendar days are not enough.',
      deeper: [
        'The plan does not use a 90% germination bar. C/N alone is not a pass. A microbe count is not a pass.',
        'Mature screened compost fines are the finish crew. Add them on Path A if the scores lag. They are mandatory if Path B was used. Planning dose: 2% by volume.',
        'Immature compost labeled “fines” does not count. A high-salt lot fails.',
        'The product claim still has to beat native compost. Heat without this cure is not a finished soil amendment.'
      ]
    },
    screen: {
      chip: 'Screen',
      name: 'Screen and contaminants',
      tags: ['proven'],
      summary: 'Bits of plastic, glass, and metal that survive are still physical junk. Biology is not a filter screen. Anything meant for land has to be screened, and the contaminant share has to be faced honestly. The clean mound in the view is an amendment candidate only if the finish tests pass and the overs are actually pulled out.',
      deeper: [
        'For the later unsorted pad test, the working screen start is about 10–15 mm. Glass and metal go to the overs.',
        'Metals do not rot away. As the organics shrink, metals can become more concentrated.',
        'Physical plastics in compost are a known way microplastics reach soil if dirty product is land-applied.',
        'Plastic pieces in the overs are feedstock for the research track, not silent proof that plastic biodegraded.'
      ]
    },
    track2: {
      chip: 'Track 2 bay',
      name: 'Track 2 hard-fraction bay',
      tags: ['speculative'],
      summary: 'Plastics, glass, and metal leave the crusher into a separate research bay. They do not block the compost pilots, and they are not the scoreboard for “did we make soil?” First priority is common durable plastics such as polyethylene and polypropylene. Glass is a weaker idea. Metals have mining-lab literature that is not household-pile proof.',
      deeper: [
        'Open-pile disappearance of grocery-bag plastics is, in the reviews this plan trusts, speculative to nearly unproven.',
        'A lab win on polyester (PET) is a different chemistry. Do not treat it as proof that polyethylene bags will vanish.',
        'Honest assays mean labeled carbon (carbon-13) or a real mass balance against twins that weather with no biology. A sticky film and a lighter scrap are not a result.',
        'If selection experiments happen, they sit beside the working pile, on environmental strains. Not a synthetic-biology shop, and not a pathogen program.',
        'Wood-rot fungi stay in this bay. They are not mixed into the Wave 1 field pack.'
      ]
    },
    r1: {
      chip: 'R1 · G1',
      name: 'R1 · Bacillus-group pioneers',
      tags: ['proven', 'hold'],
      summary: 'Rank 1 is the pioneer crew: Bacillus-group compost bacteria. They take the easy meal in the food fraction — sugars, starch, protein, and plant oils. The pile can warm up. That early crash is useful. It clears the counter for the fiber crew. This is a role under purchase hold, not a product to buy.',
      deeper: [
        'They go in at the start, inside the Path A dry pack.',
        'The gate is food mass loss against a matched pile with no inoculum. Heat is supporting evidence only.',
        'They need oxygen and 50–60% moisture. Very wet food without paper or yard bulk collapses the air spaces.',
        'Meat and dairy are out of the Wave 1 food recipe.',
        'They are not a claim about eating polyethylene. On the plastics track they are only a biomass builder, and only after the organics are gone.'
      ]
    },
    r2r4: {
      chip: 'R2–R4 · G2',
      name: 'R2–R4 · fiber crew',
      tags: ['proven', 'hold'],
      summary: 'Ranks 2, 3, and 4 are the heat-tolerant fiber crew. Thermobifida-class and Streptomyces-class actinobacteria, plus a thermotolerant cellulolytic Bacillus, cut cellulose and hemicellulose in paper, yard, and the mixed blend while the pile is hot. The paper coupon has to move. A headcount of one genus is not the gate.',
      deeper: [
        'They ride in the same start-of-pile dry pack as rank 1. On Path B they can be the water-only slurry, still with no fungi in that slurry.',
        'Rank 2’s primary proof is a paper fiber coupon versus the zero twin. That coupon blocks the Cascade if it fails. Rank 4 also carries the heat diagnostic on the mixed blend.',
        'Dry-out stops them. Remoisten the whole bay, including controls.',
        'They can suppress fungi, which is why any fungus assist waits until the pile has cooled.',
        'For the plastics bay they are only a seed for later contained tests, not proof that plastic is gone.'
      ]
    },
    r5: {
      chip: 'R5 · ≤20%',
      name: 'R5 · optional Trichoderma sliver',
      tags: ['plan', 'hold'],
      summary: 'Rank 5 is an optional sliver of Trichoderma-class fungus blended into the fiber pack at the start. The cap is 20% of that fiber crew’s propagule mass, so the drawing shows it shorter. The bacteria and actinobacteria stay the majority. This fungus does not get to carry the fiber result by itself.',
      deeper: [
        'The parent fiber coupon still has to pass. Rank 5 never carries the knife alone.',
        'The 20% cap is a design fraction Corey froze as allowed, not a magic ratio from a single paper.',
        'It is sensitive to a long hot core. It expects the bacterial partners to take the heat.',
        'It is not a substitute for the later cool-down dose, and it is never packed with wood-rot fungi.',
        'If it fights the fiber crew, drop it and keep ranks 2–4. That choice can wait.'
      ]
    },
    r6: {
      chip: 'R6a / R6b',
      name: 'R6a or R6b · after cool-down',
      tags: ['plan', 'hold'],
      summary: 'After the core is below about 40°C, Path A may add one post-cool assist, in its own test series. Rank 6a is a Trichoderma-class dose. Rank 6b is weathered spent substrate from oyster-mushroom growing, not a live wood-rot culture. Pick one arm. Never blend them.',
      deeper: [
        '6a planning dose: 0.2% by weight. 6b planning dose: 5% by volume, after a salt and maturity check. The plan prefers a low-salt lot.',
        'The gate is a real change versus the staged parent pile, without making the germination test worse.',
        'A drop of about 30% or more in the fiber coupon kills that series in combination.',
        'Mushroom leftover is a dose-sensitive soil helper in the literature. It is not an open-pile plastic mineralizer.',
        'Skipping both and going straight to finish fines is an allowed lean Path A.'
      ]
    },
    r7: {
      chip: 'R7 · G4',
      name: 'R7 · finish fines',
      tags: ['proven', 'hold'],
      summary: 'Rank 7 is mature, screened compost fines. They are not the crew that eats the waste. They finish the pile so it is safer for plants. On Path A, add them if germination or carbon-to-nitrogen is lagging. If Path B’s hot slurry was used, this step is mandatory.',
      deeper: [
        'Planning dose at cure: 2% by volume. The lot should be identifiable. Measure salt, carbon-to-nitrogen, and germination on it when you can.',
        'Pass is a germination index of at least 80% and carbon-to-nitrogen near 10–20.',
        'High-salt fines fail. Immature compost labeled “fines” is not this rank.',
        'The product claim still has to beat native compost. These fines keep the land-apply story honest while plastics research runs beside it.'
      ]
    },
    f: {
      chip: 'Food',
      name: 'F · food',
      tags: ['plan'],
      summary: 'Food is the easiest efficiency test, and the one most likely to crown a pack that later fails on paper. The Wave 1 start, by wet mass, is about half produce and vegetable scraps, a quarter cooled cooked starch, a tenth coffee or tea, and the rest soft green trimmings.',
      deeper: [
        'Meat, dairy, bones, and large pits stay out of version 1.',
        'Drain free liquid. Do not squeeze it bone-dry. After inoculum water, aim for 50–60% moisture.',
        'Chop to about 30 mm. Freeze day-batches, thaw overnight, remix before weighing.',
        'Rank 1 is the primary proof here. Do not ship a community on a food-only win.',
        'Ratios are locked starting points. Variants wait until the base advances, and they are capped so they do not eat the bin budget.'
      ]
    },
    p: {
      chip: 'Paper / card',
      name: 'P · paper and cardboard',
      tags: ['plan'],
      summary: 'Paper and cardboard are the fiber test. The start is mostly unwaxed shipping cardboard (about 70%) plus plain office paper or newsprint (about 30%), shredded to about 50 mm. Waxed, glossy, and plastic-coated stock are later variants, not the base.',
      deeper: [
        'It starts dry. Bring it to 50–60% moisture when the inoculum goes in.',
        'Alone, cardboard is extremely carbon-heavy. That is fine for a solo fiber proof. It is not a land-apply mix.',
        'The rank 2 coupon on this recipe is the knife that has to work before the Cascade advances.',
        'Remove tape and labels when that is easy. Coatings are not invisible.'
      ]
    },
    y: {
      chip: 'Yard',
      name: 'Y · soft yard',
      tags: ['plan'],
      summary: 'Soft yard is the third base recipe: about 60% leaves and 40% grass clippings, chopped, with fresh and wilted grass mixed so it does not mat into slime. It is a secondary fiber proof and the honesty check inside the mixed blend.',
      deeper: [
        'Woody stems thicker than about 5 mm, and obviously diseased piles, stay out of the base.',
        'Moisture after wet-up: 50–60%.',
        'Grass-heavy and leaf-heavy variants wait until the base advances.'
      ]
    },
    m: {
      chip: 'Mixed',
      name: 'M · mixed',
      tags: ['plan'],
      summary: 'Mixed is the community and freeze recipe. Start from the base recipes at about 40% food, 40% paper, and 20% yard, by wet mass. Then trim the paper until the estimated carbon-to-nitrogen sits around 25–40, aiming near 30. Cardboard moves that ratio a lot.',
      deeper: [
        'This is the feedstock for Path A drafts, the finish-fines tests, the native control, and the freeze gate.',
        'Moisture 50–60% after inoculum.',
        'Mix only what the staggered bins need. Peak concurrent bins are 48 by default, 60 at the ceiling.',
        'The zero twins get the same water and the same turning.',
        'A community that wins on mixed maturity but loses food speed can be an acceptable trade if the freeze score is maturity. Log it. A community that kills the paper coupon does not ship.'
      ]
    },
    s0a: {
      chip: 'S0a',
      name: 'S0a · knives',
      tags: ['plan'],
      summary: 'S0a asks a blunt question: do the knives cut? Solo roles meet base food, paper, and mixed recipes, each beside a twin with no inoculum. The fiber coupon is the gate. If the paper test does not clearly beat the zero pile, Path A does not advance.',
      deeper: [
        'The first block is those knives, on the order of a few dozen bins, not every planned cell on day zero.',
        'A provisional “clearly better than zero” bar gets calibrated in that first block. It is not a law of nature, and heat alone does not pass the food knife.',
        'Finish fines on mixed must reach a germination index of at least 80% and carbon-to-nitrogen near 10–20 before anyone talks about freezing a recipe.',
        'Cool-down assists run as separate series. Same-class pairs come before the full community.',
        'A failed solo cell is cut. It does not get carried into the mix on hope.'
      ]
    },
    s0b: {
      chip: 'S0b',
      name: 'S0b · Path A draft',
      tags: ['plan'],
      summary: 'S0b is the Path A draft on the mixed recipe. The full Cascade has to live together. It must beat native compost and the zero pile on the maturity bundle, and it must keep at least one of the food or paper functions it already won.',
      deeper: [
        'Planning scale is a live rotation, staggered, with a default ceiling of 48 bins at once and a hard ceiling of 60. Not everything on day one.',
        'If the community kills a solo win, restage timing or dose. Never average a food win with a paper win.',
        'A few single-lever iterations, then the draft is killed if it still fails.',
        'Open choices that do not block this phase: the 20% fungus sliver on or off, and 6a versus 6b versus neither.'
      ]
    },
    s0c: {
      chip: 'S0c',
      name: 'S0c · freeze',
      tags: ['plan'],
      summary: 'S0c freezes a candidate. Two rounds in a row, on a clean food-paper-yard mix. Frozen Path A — or Path B plus mandatory finish fines — has to beat native compost and the empty twin on a germination index of at least 80% and carbon-to-nitrogen near 10–20.',
      deeper: [
        'The grid is small: frozen A, B plus finish fines, native compost, and none.',
        'Miss the bar and you get a few single-lever tweaks, then a redesign. The finish line does not move to a vibe.',
        'The unsorted pad stays closed until this freeze exists.'
      ]
    },
    t0: {
      chip: 'T0',
      name: 'T0 · unsorted pad',
      tags: ['plan', 'hold'],
      summary: 'T0 is the field pad, and only after the freeze. Bagged unsorted trash goes through a shredder. Frozen Path A is compared with native compost and with crush-only. A final screen, starting around 10–15 mm, separates an amendment candidate from the overs. This page does not open that pad.',
      deeper: [
        'Optional Path B can ride along. Track 2 plastics are measured on the side and are not this test’s victory.',
        'The pack has to beat native compost and crush-only on maturity, or it does not become the field recipe.',
        'A messy personal-bag dress rehearsal can sit between the freeze and full T0. It does not replace the clean base recipes.',
        'Purchase hold still applies. T0 here is a gated plan, not a start date.'
      ]
    },
    t2phase: {
      chip: 'Track 2',
      name: 'Track 2 phase · parallel',
      tags: ['speculative'],
      summary: 'Track 2 runs beside the compost line the whole time and never gates it. Contained tests, plastics first. Success is a carbon-13 result or a mass balance that beats a no-biology twin. It does not move the land-apply score.',
      deeper: [
        'Wood-rot roles stay in contained boxes. They are not mixed into the Wave 1 field pack.',
        'Glass and metal are exploratory only.',
        'The pad test waits on the S0c freeze, not on this plastics work. This work also does not get to pretend the pad already passed.',
        'Cameras and gas meters are never gates on either track.'
      ]
    }
  };

  var PROCESS = ['bags', 'crush', 'zero', 'room', 'pathA', 'pathB', 'pathD', 'heat', 'cool', 'cure', 'screen', 'track2'];
  var CREW = ['r1', 'r2r4', 'r5', 'r6', 'r7'];
  var FEED = ['f', 'p', 'y', 'm'];
  var PHASE = ['s0a', 's0b', 's0c', 't0', 't2phase'];

  var DEFAULT_TITLE = 'Click any piece';
  var DEFAULT_BODY = 'Stations, crew chips, feedstock chips, and the phase strip open the same card: a short note, then Deeper for gates and planning numbers. Purchase stays on hold.';

  var api = null;

  function tagLabel(tag) {
    switch (tag) {
      case 'proven':
        return 'Proven';
      case 'speculative':
        return 'Speculative';
      case 'plan':
        return 'Locked plan';
      case 'hold':
        return 'Purchase HOLD';
      default: {
        var _never = tag;
        return String(_never);
      }
    }
  }

  function mountChips() {
    var mount = document.getElementById('chip-mount');
    var groups = [
      ['Process', PROCESS],
      ['Path A crew', CREW],
      ['Feedstock · Wave 1 starts', FEED]
    ];
    groups.forEach(function (group) {
      var heading = document.createElement('h3');
      heading.textContent = group[0];
      var row = document.createElement('div');
      row.className = 'chip-row';
      group[1].forEach(function (id) {
        var item = ITEMS[id];
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'chip' + (item.tags.indexOf('speculative') >= 0 ? ' spec' : '');
        btn.dataset.hotspot = id;
        btn.textContent = item.chip;
        btn.setAttribute('aria-pressed', 'false');
        row.appendChild(btn);
      });
      mount.appendChild(heading);
      mount.appendChild(row);
    });
  }

  function setDeeperOpen(open) {
    var btn = document.getElementById('btn-deeper');
    var list = document.getElementById('detail-deeper');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.textContent = open ? 'Hide deeper' : 'Deeper';
    list.hidden = !open;
  }

  function select(id, opts) {
    opts = opts || {};
    var item = id ? ITEMS[id] : null;
    var title = document.getElementById('detail-title');
    var summary = document.getElementById('detail-summary');
    var tags = document.getElementById('detail-tags');
    var deeper = document.getElementById('detail-deeper');
    var deeperBtn = document.getElementById('btn-deeper');
    var fsTitle = document.getElementById('fs-title');
    var fsBody = document.getElementById('fs-body');

    document.querySelectorAll('button[data-hotspot]').forEach(function (el) {
      el.setAttribute('aria-pressed', item && el.getAttribute('data-hotspot') === id ? 'true' : 'false');
    });

    tags.replaceChildren();
    deeper.replaceChildren();

    if (!item) {
      title.textContent = DEFAULT_TITLE;
      summary.textContent = DEFAULT_BODY;
      deeperBtn.hidden = true;
      setDeeperOpen(false);
      fsTitle.textContent = 'Click a station';
      fsBody.textContent = 'Bags, the crusher, the pile, the screen, or the research bay.';
      if (api) api.focusHotspot(null);
      return;
    }

    item.tags.forEach(function (tag) {
      var pill = document.createElement('span');
      pill.className = 'tag ' + tag;
      pill.textContent = tagLabel(tag);
      tags.appendChild(pill);
    });
    title.textContent = item.name;
    summary.textContent = item.summary;
    item.deeper.forEach(function (line) {
      var li = document.createElement('li');
      li.textContent = line;
      deeper.appendChild(li);
    });
    deeperBtn.hidden = item.deeper.length === 0;
    setDeeperOpen(false);
    fsTitle.textContent = item.name;
    fsBody.textContent = item.summary;
    if (api) api.focusHotspot(id);

    if (opts.scroll && !document.body.classList.contains('fs-3d') && window.innerWidth <= 860) {
      document.getElementById('detail').scrollIntoView({ block: 'nearest' });
    }
  }

  function activateTab(tab, focusTab) {
    var id = tab.getAttribute('data-tab');
    var buttons = Array.prototype.slice.call(document.querySelectorAll('nav.tabs [role="tab"]'));
    var mainEl = document.getElementById('main');
    buttons.forEach(function (btn) {
      var on = btn === tab;
      btn.setAttribute('aria-selected', on ? 'true' : 'false');
      btn.tabIndex = on ? 0 : -1;
    });
    ['action', 'honesty', 'wave', 'score'].forEach(function (key) {
      var panel = document.getElementById('panel-' + key);
      var on = key === id;
      panel.classList.toggle('active', on);
      panel.setAttribute('aria-hidden', on ? 'false' : 'true');
      if ('inert' in panel) panel.inert = !on;
    });
    var schematic = id === 'action';
    mainEl.classList.toggle('is-3d', schematic);
    document.body.classList.toggle('is-schematic', schematic);
    mainEl.scrollTop = 0;
    if (schematic && api) {
      requestAnimationFrame(function () { api.resize(); });
    }
    if (focusTab) tab.focus();
    if (window.history && window.history.replaceState) {
      var next = schematic ? location.pathname : location.pathname + '#' + id;
      if ((location.pathname + location.hash) !== next && (location.hash || !schematic)) {
        window.history.replaceState(null, '', schematic ? location.pathname : '#' + id);
      }
    }
  }

  function initTabs() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('nav.tabs [role="tab"]'));
    var tablist = document.querySelector('nav.tabs');
    tablist.addEventListener('keydown', function (ev) {
      var i = buttons.indexOf(document.activeElement);
      if (i < 0) return;
      var next = -1;
      switch (ev.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          next = (i + 1) % buttons.length;
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          next = (i - 1 + buttons.length) % buttons.length;
          break;
        case 'Home':
          next = 0;
          break;
        case 'End':
          next = buttons.length - 1;
          break;
        default: {
          var _exhaustive = ev.key;
          void _exhaustive;
          return;
        }
      }
      ev.preventDefault();
      activateTab(buttons[next], true);
    });
    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () { activateTab(btn, true); });
    });
    document.body.classList.add('is-schematic');
    var hash = (location.hash || '').replace('#', '');
    if (hash === 'honesty' || hash === 'wave' || hash === 'score') {
      var match = document.querySelector('nav.tabs [data-tab="' + hash + '"]');
      if (match) activateTab(match, false);
    }
  }

  function initChrome() {
    mountChips();
    PROCESS.concat(CREW, FEED, PHASE).forEach(function (id) {
      if (!ITEMS[id] || !ITEMS[id].summary || !ITEMS[id].deeper) {
        throw new Error('LitterSoil copy missing for ' + id);
      }
    });
    document.body.addEventListener('click', function (ev) {
      var btn = ev.target.closest('button[data-hotspot]');
      if (!btn) return;
      select(btn.getAttribute('data-hotspot'), { scroll: true });
    });
    document.getElementById('btn-deeper').addEventListener('click', function () {
      var open = document.getElementById('btn-deeper').getAttribute('aria-expanded') === 'true';
      setDeeperOpen(!open);
    });
    initTabs();

    function relayout() { if (api) api.resize(); }
    function enterFs() {
      document.body.classList.add('fs-3d');
      document.getElementById('fs-hud').hidden = false;
      requestAnimationFrame(function () { relayout(); requestAnimationFrame(relayout); });
    }
    function exitFs() {
      document.body.classList.remove('fs-3d');
      document.getElementById('fs-hud').hidden = true;
      requestAnimationFrame(function () { relayout(); requestAnimationFrame(relayout); });
    }
    document.getElementById('btn-expand').addEventListener('click', enterFs);
    document.getElementById('btn-fs-close').addEventListener('click', exitFs);
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && document.body.classList.contains('fs-3d')) {
        exitFs();
        ev.preventDefault();
      }
    });
  }

  function showBootError(msg) {
    var loading = document.getElementById('three-loading');
    var err = document.getElementById('three-error');
    if (loading) loading.classList.add('hidden');
    if (!err) return;
    err.classList.add('visible');
    err.innerHTML = '<strong>3D viewer failed to load</strong><br/>' + String(msg).replace(/</g, '&lt;');
  }

  function boot(THREE, OrbitControls) {
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var wrap = document.getElementById('canvas-wrap');
    var loading = document.getElementById('three-loading');

    var scene = new THREE.Scene();
    scene.background = new THREE.Color(0x12151a);
    scene.fog = new THREE.Fog(0x12151a, 38, 82);

    var camera = new THREE.PerspectiveCamera(38, 1, 0.1, 200);
    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    var coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, coarse ? 1.75 : 2));
    if (renderer.outputColorSpace !== undefined && THREE.SRGBColorSpace) {
      renderer.outputColorSpace = THREE.SRGBColorSpace;
    } else if (renderer.outputEncoding !== undefined && THREE.sRGBEncoding !== undefined) {
      renderer.outputEncoding = THREE.sRGBEncoding;
    }
    wrap.appendChild(renderer.domElement);

    var controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;
    controls.minDistance = 5;
    controls.maxDistance = 70;
    controls.maxPolarAngle = Math.PI * 0.49;
    if ('screenSpacePanning' in controls) controls.screenSpacePanning = true;
    if ('enableKeys' in controls) controls.enableKeys = false;
    if (THREE.TOUCH) {
      controls.touches.ONE = THREE.TOUCH.ROTATE;
      controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;
    }

    scene.add(new THREE.AmbientLight(0xf4f7f2, 0.55));
    scene.add(new THREE.HemisphereLight(0xd5e6d4, 0x1a1612, 0.45));
    var key = new THREE.DirectionalLight(0xfff7ee, 0.95);
    key.position.set(12, 18, 10);
    scene.add(key);
    var rim = new THREE.DirectionalLight(0x6ee7a8, 0.35);
    rim.position.set(-12, 8, -6);
    scene.add(rim);
    var warm = new THREE.DirectionalLight(0xfb923c, 0.22);
    warm.position.set(-2, 6, 4);
    scene.add(warm);

    var floor = new THREE.Mesh(
      new THREE.CircleGeometry(30, 48),
      new THREE.MeshStandardMaterial({ color: 0x161b20, roughness: 1, metalness: 0 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.22;
    scene.add(floor);
    var grid = new THREE.GridHelper(46, 23, 0x2d4638, 0x1c2622);
    grid.position.y = -0.2;
    scene.add(grid);

    var matPlinth = new THREE.MeshStandardMaterial({ color: 0x1c2420, roughness: 0.92, metalness: 0.04 });
    var matRoad = new THREE.MeshStandardMaterial({ color: 0x234237, roughness: 0.8, metalness: 0.02 });
    var matSide = new THREE.MeshStandardMaterial({ color: 0x3a3158, roughness: 0.75, metalness: 0.04 });
    var matSoil = new THREE.MeshStandardMaterial({ color: 0x6b4a32, roughness: 0.92, metalness: 0 });
    var matSoilDark = new THREE.MeshStandardMaterial({ color: 0x3e2a1c, roughness: 0.94, metalness: 0 });
    var matFace = new THREE.MeshStandardMaterial({ color: 0x8b6244, roughness: 0.88, metalness: 0 });
    var matFiber = new THREE.MeshStandardMaterial({ color: 0xd6b483, roughness: 0.8, metalness: 0 });
    var matCore = new THREE.MeshStandardMaterial({
      color: 0xf97316, emissive: 0x9a3412, emissiveIntensity: 0.45, roughness: 0.45, metalness: 0.05
    });
    var matAir = new THREE.MeshStandardMaterial({ color: 0xbae6fd, roughness: 0.4, metalness: 0.1 });
    var matWater = new THREE.MeshStandardMaterial({
      color: 0x7dd3fc, emissive: 0x0c4a6e, emissiveIntensity: 0.2, roughness: 0.25, metalness: 0.05
    });
    var matSteel = new THREE.MeshStandardMaterial({ color: 0x9aa3ad, metalness: 0.55, roughness: 0.38 });
    var matSteelDark = new THREE.MeshStandardMaterial({ color: 0x5c6770, metalness: 0.45, roughness: 0.45 });
    var matRoller = new THREE.MeshStandardMaterial({ color: 0xc5ced6, metalness: 0.62, roughness: 0.32 });
    var matBag = new THREE.MeshStandardMaterial({ color: 0x4b5563, roughness: 0.8, metalness: 0.05 });
    var matFilm = new THREE.MeshStandardMaterial({
      color: 0xd5dde6, roughness: 0.35, metalness: 0.15, transparent: true, opacity: 0.8, side: THREE.DoubleSide
    });
    var matFood = new THREE.MeshStandardMaterial({ color: 0x3f6b45, roughness: 0.75, metalness: 0 });
    var matPaper = new THREE.MeshStandardMaterial({ color: 0xd9c7a6, roughness: 0.8, metalness: 0 });
    var matYard = new THREE.MeshStandardMaterial({ color: 0x4d7c3a, roughness: 0.8, metalness: 0 });
    var matMixed = new THREE.MeshStandardMaterial({ color: 0x8a6a3b, roughness: 0.78, metalness: 0 });
    var matPack = new THREE.MeshStandardMaterial({ color: 0x6ee7a8, roughness: 0.5, metalness: 0.08, emissive: 0x14532d, emissiveIntensity: 0.18 });
    var matHotBin = new THREE.MeshStandardMaterial({ color: 0xea580c, roughness: 0.55, metalness: 0.08, emissive: 0x7c2d12, emissiveIntensity: 0.25 });
    var matNative = new THREE.MeshStandardMaterial({ color: 0x78716c, roughness: 0.9, metalness: 0 });
    var matZero = new THREE.MeshStandardMaterial({ color: 0x57534e, roughness: 0.9, metalness: 0.05 });
    var matGlass = new THREE.MeshStandardMaterial({
      color: 0xc4b5fd, transparent: true, opacity: 0.18, roughness: 0.08, metalness: 0.1, side: THREE.DoubleSide
    });
    var matShard = new THREE.MeshStandardMaterial({ color: 0x67e8f9, roughness: 0.15, metalness: 0.2, emissive: 0x155e75, emissiveIntensity: 0.2 });
    var matCan = new THREE.MeshStandardMaterial({ color: 0xe5e7eb, metalness: 0.75, roughness: 0.28 });
    var matSprout = new THREE.MeshStandardMaterial({ color: 0x86efac, roughness: 0.55, metalness: 0 });
    var matCool = new THREE.MeshStandardMaterial({ color: 0x7c5c44, roughness: 0.9, metalness: 0 });
    var matPass = new THREE.MeshStandardMaterial({ color: 0x8fbc6b, roughness: 0.85, metalness: 0 });
    var matChevron = new THREE.MeshStandardMaterial({ color: 0x3d8f6a, roughness: 0.6, metalness: 0.05 });

    var pickables = [];
    var anchors = {};
    var labelSprites = [];
    var rollers = [];
    var airSpin = null;
    var coreMesh = null;

    function box(w, h, d, mat, x, y, z) {
      var mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
      mesh.position.set(x || 0, y || 0, z || 0);
      return mesh;
    }

    function tagTree(root, id) {
      root.traverse(function (obj) {
        if (obj.isMesh) {
          obj.userData.hotspot = id;
          pickables.push(obj);
        }
      });
    }

    function register(id, obj, ring) {
      anchors[id] = obj;
      obj.userData.ring = ring || 1;
    }

    function roundRect(ctx, x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }

    function makeLabel(text, x, y, z, tint, labelScale) {
      var canvas = document.createElement('canvas');
      canvas.width = 768;
      canvas.height = 192;
      var ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, 768, 192);
      ctx.fillStyle = 'rgba(18, 21, 26, 0.84)';
      roundRect(ctx, 16, 36, 736, 120, 24);
      ctx.fill();
      ctx.font = '700 56px system-ui, sans-serif';
      ctx.fillStyle = tint || '#d7fbe8';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, 384, 96);
      var tex = new THREE.CanvasTexture(canvas);
      if (tex.colorSpace !== undefined && THREE.SRGBColorSpace) tex.colorSpace = THREE.SRGBColorSpace;
      var spr = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
      spr.position.set(x, y, z);
      var drawn = labelScale || (text.length > 16 ? 2.7 : 1.9);
      spr.scale.set(drawn, drawn * 0.25, 1);
      spr.renderOrder = 10;
      scene.add(spr);
      labelSprites.push(spr);
      return spr;
    }

    var plinth = box(34, 0.28, 11, matPlinth, -1, -0.14, 0.2);
    scene.add(plinth);
    var road = box(29.5, 0.05, 1.35, matRoad, -1.2, 0.02, 0);
    scene.add(road);

    [-13.2, -9.2, -4.6, 0.2, 4.2, 8.0].forEach(function (x) {
      var chev = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.34, 3), matChevron);
      chev.rotation.z = -Math.PI / 2;
      chev.position.set(x, 0.1, 0);
      scene.add(chev);
    });

    /* Bags + feedstock crates */
    var bags = new THREE.Group();
    bags.position.set(-15, 0, 0);
    var sack = new THREE.Mesh(new THREE.SphereGeometry(0.58, 18, 14), matBag);
    sack.scale.set(1.35, 0.9, 0.85);
    sack.position.set(0, 0.95, -0.15);
    bags.add(sack);
    var film = new THREE.Mesh(new THREE.PlaneGeometry(1.55, 0.55), matFilm);
    film.position.set(0.05, 0.72, 0.48);
    film.rotation.x = -0.3;
    bags.add(film);
    var crateSpecs = [
      ['f', matFood, -0.58, 0.95],
      ['p', matPaper, 0.58, 0.95],
      ['y', matYard, -0.58, 0.22],
      ['m', matMixed, 0.58, 0.22]
    ];
    crateSpecs.forEach(function (spec) {
      var crate = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.46, 0.58), spec[1]);
      crate.position.set(spec[2], 0.23, spec[3]);
      bags.add(crate);
      tagTree(crate, spec[0]);
      register(spec[0], crate, 0.62);
      var crateHit = new THREE.Mesh(
        new THREE.SphereGeometry(0.42, 8, 6),
        new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false })
      );
      crateHit.position.copy(crate.position);
      crateHit.position.y = 0.4;
      bags.add(crateHit);
      crateHit.userData.hotspot = spec[0];
      pickables.push(crateHit);
    });
    tagTree(sack, 'bags');
    tagTree(film, 'bags');
    register('bags', bags, 1.35);
    scene.add(bags);

    /* Crusher */
    var crush = new THREE.Group();
    crush.position.set(-11, 0, 0);
    crush.add(box(0.12, 1.55, 0.12, matSteelDark, 0, 0.78, -0.7));
    crush.add(box(0.12, 1.55, 0.12, matSteelDark, 0, 0.78, 0.7));
    crush.add(box(1.15, 0.12, 1.55, matSteel, 0, 1.55, 0));
    [-0.24, 0.24].forEach(function (x) {
      var spin = new THREE.Group();
      spin.position.set(x, 0.92, 0);
      var roller = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.26, 1.2, 22), matRoller);
      roller.rotation.x = Math.PI / 2;
      spin.add(roller);
      crush.add(spin);
      rollers.push(spin);
    });
    crush.add(box(1.05, 0.28, 1.25, matSteelDark, 0, 1.9, 0));
    tagTree(crush, 'crush');
    register('crush', crush, 1.15);
    scene.add(crush);

    var zero = new THREE.Group();
    zero.position.set(-11.15, 0, 1.55);
    var zeroCup = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.36, 0.5, 10), matZero);
    zeroCup.position.y = 0.25;
    zero.add(zeroCup);
    tagTree(zero, 'zero');
    register('zero', zero, 0.7);
    var zeroHit = new THREE.Mesh(
      new THREE.SphereGeometry(0.48, 8, 6),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false })
    );
    zeroHit.position.y = 0.35;
    zero.add(zeroHit);
    zeroHit.userData.hotspot = 'zero';
    pickables.push(zeroHit);
    scene.add(zero);

    /* Inoculum: Path A pack, with B and D beside it */
    var inoc = new THREE.Group();
    inoc.position.set(-7, 0, 0);
    var trough = box(1.7, 0.28, 0.85, matSoil, 0, 0.14, 0);
    inoc.add(trough);
    var dose = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.32, 0.55, 6), matPack);
    dose.position.set(0, 0.85, -0.15);
    inoc.add(dose);
    var roleColors = { r1: 0xf5d78e, r2r4: 0xe07a3d, r5: 0xc4b5fd, r6: 0x8b7ec8, r7: 0x6ee7a8 };
    ['r1', 'r2r4', 'r5', 'r6', 'r7'].forEach(function (id, i) {
      var cap = new THREE.Group();
      var mat = new THREE.MeshStandardMaterial({ color: roleColors[id], roughness: 0.42, metalness: 0.06 });
      var h = id === 'r5' ? 0.26 : 0.48;
      var body = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, h, 12), mat);
      body.position.y = 0.16 + h / 2;
      var capTop = new THREE.Mesh(new THREE.SphereGeometry(0.11, 12, 8), mat);
      capTop.position.y = 0.16 + h;
      cap.add(body, capTop);
      cap.position.set(-0.72 + i * 0.36, 0.28, id === 'r6' ? 0.46 : 0.05);
      inoc.add(cap);
      tagTree(cap, id);
      register(id, cap, 0.5);
      var roleHit = new THREE.Mesh(
        new THREE.SphereGeometry(0.26, 8, 6),
        new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false })
      );
      roleHit.position.y = 0.42;
      cap.add(roleHit);
      roleHit.userData.hotspot = id;
      pickables.push(roleHit);
    });
    tagTree(trough, 'pathA');
    tagTree(dose, 'pathA');
    register('pathA', inoc, 1.25);
    scene.add(inoc);

    function jar(mat, id, x, z) {
      var g = new THREE.Group();
      var cup = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.34, 0.5, 12), mat);
      cup.position.y = 0.25;
      var fill = new THREE.Mesh(new THREE.SphereGeometry(0.22, 14, 10), mat);
      fill.scale.y = 0.55;
      fill.position.y = 0.46;
      g.add(cup, fill);
      g.position.set(x, 0, z);
      tagTree(g, id);
      register(id, g, 0.65);
      scene.add(g);
      return g;
    }
    jar(matHotBin, 'pathB', -6.05, 1.55);
    jar(matNative, 'pathD', -7.95, 1.55);

    /* Hot cutaway */
    var heat = new THREE.Group();
    heat.position.set(-2.1, 0, 0);
    var shell = new THREE.Mesh(
      new THREE.SphereGeometry(1.65, 32, 20, 0, Math.PI * 2, 0, Math.PI / 2),
      matSoil
    );
    shell.scale.set(1.15, 1, 0.72);
    shell.position.z = -0.5;
    heat.add(shell);
    var face = new THREE.Group();
    face.position.set(0, 1.05, 1.05);
    var skin = new THREE.Mesh(new THREE.CircleGeometry(1.02, 40), matFace);
    var fiberDisc = new THREE.Mesh(new THREE.CircleGeometry(0.68, 32), matFiber);
    fiberDisc.position.z = 0.02;
    coreMesh = new THREE.Mesh(new THREE.CircleGeometry(0.38, 28), matCore);
    coreMesh.position.z = 0.04;
    face.add(skin, fiberDisc, coreMesh);
    [[-0.42, 0.22], [0.36, -0.18], [0.08, 0.48]].forEach(function (p) {
      var pocket = new THREE.Mesh(new THREE.CircleGeometry(0.08, 12), matAir);
      pocket.position.set(p[0], p[1], 0.06);
      face.add(pocket);
    });
    heat.add(face);
    var room = new THREE.Group();
    room.position.set(1.45, 1.85, 0.55);
    var drop = new THREE.Mesh(new THREE.SphereGeometry(0.16, 14, 10), matWater);
    drop.scale.set(0.8, 1.2, 0.8);
    drop.position.x = -0.48;
    airSpin = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.045, 8, 18), matAir);
    airSpin.rotation.x = Math.PI / 2;
    var beam = box(0.34, 0.05, 0.05, matPaper, 0.5, 0, 0);
    var panL = box(0.07, 0.16, 0.07, matPaper, 0.34, 0.08, 0);
    var panR = box(0.07, 0.16, 0.07, matFood, 0.66, 0.08, 0);
    room.add(drop, airSpin, beam, panL, panR);
    heat.add(room);
    tagTree(shell, 'heat');
    tagTree(face, 'heat');
    var roomHit = new THREE.Mesh(
      new THREE.SphereGeometry(0.62, 8, 6),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false })
    );
    room.add(roomHit);
    roomHit.userData.hotspot = 'room';
    pickables.push(roomHit);
    tagTree(room, 'room');
    register('heat', heat, 1.7);
    register('room', room, 0.85);
    scene.add(heat);

    /* Cool */
    var cool = new THREE.Group();
    cool.position.set(2.5, 0, 0);
    var coolMound = new THREE.Mesh(
      new THREE.SphereGeometry(1.05, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2),
      matCool
    );
    coolMound.scale.y = 0.8;
    cool.add(coolMound);
    var tokenA = new THREE.Mesh(new THREE.SphereGeometry(0.16, 12, 10), new THREE.MeshStandardMaterial({ color: 0xc4b5fd, roughness: 0.45 }));
    tokenA.position.set(-0.22, 0.95, 0.35);
    var tokenB = new THREE.Mesh(new THREE.SphereGeometry(0.16, 12, 10), new THREE.MeshStandardMaterial({ color: 0xd6b483, roughness: 0.6 }));
    tokenB.position.set(0.22, 0.95, 0.35);
    cool.add(tokenA, tokenB);
    tagTree(coolMound, 'cool');
    tagTree(tokenA, 'r6');
    tagTree(tokenB, 'r6');
    register('cool', cool, 1.15);
    scene.add(cool);

    /* Cure */
    var cure = new THREE.Group();
    cure.position.set(6.15, 0, 0);
    var cureMound = new THREE.Mesh(
      new THREE.SphereGeometry(1.0, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2),
      matSoilDark
    );
    cureMound.scale.y = 0.72;
    cure.add(cureMound);
    var stem = box(0.06, 0.45, 0.06, matSprout, 0.1, 0.85, 0.15);
    var leafL = box(0.22, 0.05, 0.1, matSprout, -0.08, 1.05, 0.15);
    var leafR = box(0.22, 0.05, 0.1, matSprout, 0.26, 1.02, 0.15);
    leafL.rotation.z = 0.5;
    leafR.rotation.z = -0.4;
    cure.add(stem, leafL, leafR);
    tagTree(cure, 'cure');
    register('cure', cure, 1.1);
    scene.add(cure);

    /* Screen + candidate mound */
    var screen = new THREE.Group();
    screen.position.set(10.7, 0, 0);
    var frame = new THREE.Group();
    frame.position.set(-0.15, 0.72, 0);
    frame.rotation.x = -0.65;
    var b;
    for (b = 0; b < 6; b += 1) {
      frame.add(box(1.35, 0.035, 0.035, matSteel, 0, 0, -0.5 + b * 0.2));
      frame.add(box(0.035, 0.035, 1.15, matSteel, -0.55 + b * 0.22, 0, 0));
    }
    screen.add(frame);
    var fines = new THREE.Group();
    [[0.15, 0.12, 0.25], [0.35, 0.1, 0.05], [0.05, 0.1, -0.05]].forEach(function (p) {
      var crumb = new THREE.Mesh(new THREE.DodecahedronGeometry(0.1, 0), matPass);
      crumb.position.set(p[0], p[1], p[2]);
      fines.add(crumb);
    });
    screen.add(fines);
    var overs = new THREE.Group();
    overs.position.set(0.35, 0.16, 1.2);
    overs.add(box(0.7, 0.22, 0.5, matSteelDark, 0, 0.1, 0));
    var scrap = new THREE.Mesh(new THREE.PlaneGeometry(0.28, 0.16), matFilm);
    scrap.position.set(-0.1, 0.28, 0.05);
    scrap.rotation.x = -0.6;
    var shard = new THREE.Mesh(new THREE.OctahedronGeometry(0.1, 0), matShard);
    shard.position.set(0.12, 0.28, -0.05);
    var can = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.16, 10), matCan);
    can.position.set(0.02, 0.3, 0.12);
    overs.add(scrap, shard, can);
    screen.add(overs);
    var passed = new THREE.Mesh(
      new THREE.SphereGeometry(0.72, 20, 14, 0, Math.PI * 2, 0, Math.PI / 2),
      matPass
    );
    passed.scale.y = 0.7;
    passed.position.set(1.7, 0, 0.15);
    screen.add(passed);
    tagTree(screen, 'screen');
    register('screen', screen, 1.5);
    scene.add(screen);

    /* Track 2 bay — thinner, off the green road, toward the camera */
    var bay = new THREE.Group();
    bay.position.set(-16.5, 0, -2.55);
    var pad = box(2.15, 0.05, 1.55, matSide, 0, 0.03, 0);
    bay.add(pad);
    var glassGeo = new THREE.BoxGeometry(1.7, 1.0, 1.15);
    var glass = new THREE.Mesh(glassGeo, matGlass);
    glass.position.y = 0.72;
    var edges = new THREE.LineSegments(new THREE.EdgesGeometry(glassGeo), new THREE.LineBasicMaterial({ color: 0xc4b5fd }));
    edges.position.y = 0.72;
    bay.add(glass, edges);
    var filmA = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.42), matFilm);
    filmA.position.set(-0.35, 0.48, 0.05);
    filmA.rotation.y = 0.5;
    var filmB = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.32), matFilm);
    filmB.position.set(-0.05, 0.38, -0.2);
    filmB.rotation.z = 0.4;
    var gShard = new THREE.Mesh(new THREE.OctahedronGeometry(0.16, 0), matShard);
    gShard.position.set(0.45, 0.28, 0.15);
    var gCan = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.26, 12), matCan);
    gCan.position.set(0.15, 0.22, -0.28);
    bay.add(filmA, filmB, gShard, gCan);
    tagTree(bay, 'track2');
    register('track2', bay, 1.35);
    scene.add(bay);

    var chuteA = -11;
    var chuteB = 0.15;
    var chuteC = -16.5;
    var chuteD = -2.55;
    var chuteDx = chuteC - chuteA;
    var chuteDz = chuteD - chuteB;
    var chuteLen = Math.sqrt(chuteDx * chuteDx + chuteDz * chuteDz);
    var chute = box(chuteLen, 0.04, 0.12, matSide, (chuteA + chuteC) / 2, 0.05, (chuteB + chuteD) / 2);
    chute.rotation.y = Math.atan2(-chuteDz, chuteDx);
    scene.add(chute);

    scene.updateMatrixWorld(true);
    function liftLabel(id, text, dy, tint, scale) {
      var pos = new THREE.Vector3();
      anchors[id].getWorldPosition(pos);
      makeLabel(text, pos.x, pos.y + dy, pos.z, tint, scale);
    }
    var labelsOn = document.getElementById('tog-labels').checked;
    liftLabel('bags', 'Bags', 1.85);
    liftLabel('f', 'F', 0.55, '#d7fbe8', 1.05);
    liftLabel('p', 'P', 0.55, '#f5e6c8', 1.05);
    liftLabel('y', 'Y', 0.55, '#d7fbe8', 1.05);
    liftLabel('m', 'M', 0.55, '#f5e6c8', 1.05);
    liftLabel('crush', 'Crush', 2.15);
    liftLabel('zero', '0', 0.85, '#d6d3d1', 1.15);
    liftLabel('pathA', 'Path A', 1.45);
    liftLabel('pathB', 'B', 0.95, '#fdba74', 1.15);
    liftLabel('pathD', 'D', 0.95, '#d6d3d1', 1.15);
    liftLabel('heat', 'Hot core', 2.35, '#fdba74');
    liftLabel('cool', 'Cool', 1.35);
    liftLabel('cure', 'Cure', 1.4);
    liftLabel('screen', 'Screen', 1.55);
    makeLabel('If it passes', 12.45, 1.15, 0.2, '#d7fbe8', 1.85);
    liftLabel('track2', 'Track 2', 1.55, '#ddd6fe', 1.7);
    labelSprites.forEach(function (spr) { spr.visible = labelsOn; });

    var ring = new THREE.Mesh(
      new THREE.TorusGeometry(0.62, 0.035, 8, 32),
      new THREE.MeshBasicMaterial({ color: 0x6ee7a8 })
    );
    ring.rotation.x = Math.PI / 2;
    ring.position.y = 0.06;
    ring.visible = false;
    scene.add(ring);

    ['bags', 'crush', 'zero', 'room', 'pathA', 'pathB', 'pathD', 'heat', 'cool', 'cure', 'screen', 'track2', 'r1', 'r2r4', 'r5', 'r6', 'r7', 'f', 'p', 'y', 'm'].forEach(function (id) {
      if (!anchors[id]) console.warn('[LitterSoil] missing anchor', id);
    });

    function focusHotspot(id) {
      var anchor = id ? anchors[id] : null;
      if (!anchor) {
        ring.visible = false;
        return;
      }
      var pos = new THREE.Vector3();
      anchor.getWorldPosition(pos);
      ring.position.set(pos.x, 0.07, pos.z);
      ring.scale.setScalar(anchor.userData.ring || 1);
      ring.visible = true;
    }

    function setPose(name) {
      var portrait = camera.aspect < 0.9;
      var pos;
      var tgt;
      if (name === 'iso') {
        pos = portrait ? [12, 16, 16] : [14, 12, 15];
        tgt = [-1, 1, 0.2];
      } else if (name === 'cut') {
        pos = portrait ? [-2, 7.5, 10] : [-2.2, 3.6, 7.4];
        tgt = [-2.1, 1.15, 0.3];
      } else if (portrait) {
        pos = [-1, 22, 20];
        tgt = [-1, 0.8, 0.4];
      } else {
        pos = [0.5, 12.2, 20.5];
        tgt = [-1.4, 0.9, -0.2];
      }
      camera.position.set(pos[0], pos[1], pos[2]);
      controls.target.set(tgt[0], tgt[1], tgt[2]);
      controls.update();
    }

    function resize() {
      var w = wrap.clientWidth || 0;
      var h = wrap.clientHeight || 0;
      if (w < 8 || h < 8) {
        var rect = wrap.getBoundingClientRect();
        w = Math.max(w, Math.round(rect.width));
        h = Math.max(h, Math.round(rect.height));
      }
      if (w < 8) w = 640;
      if (h < 8) h = 420;
      camera.fov = (w / h < 0.85) ? 52 : 38;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
    }

    document.getElementById('btn-reset').onclick = function () {
      resize();
      setPose('overview');
      select(null);
    };
    document.getElementById('btn-iso').onclick = function () { setPose('iso'); };
    document.getElementById('btn-cut').onclick = function () { setPose('cut'); };
    document.getElementById('tog-labels').addEventListener('change', function (ev) {
      labelSprites.forEach(function (spr) { spr.visible = ev.target.checked; });
    });

    var raycaster = new THREE.Raycaster();
    var pointer = new THREE.Vector2();
    var down = null;
    wrap.addEventListener('pointerdown', function (ev) {
      if (ev.button !== 0) return;
      down = { x: ev.clientX, y: ev.clientY, id: ev.pointerId };
    });
    function pick(ev) {
      var rect = renderer.domElement.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      var hits = raycaster.intersectObjects(pickables, false);
      if (!hits.length) return;
      var obj = hits[0].object;
      while (obj && obj.userData.hotspot == null) obj = obj.parent;
      if (obj && obj.userData.hotspot) select(obj.userData.hotspot, { scroll: true });
    }
    wrap.addEventListener('pointerup', function (ev) {
      if (!down || ev.pointerId !== down.id) return;
      var dx = ev.clientX - down.x;
      var dy = ev.clientY - down.y;
      down = null;
      if (dx * dx + dy * dy > 36) return;
      pick(ev);
    });
    wrap.addEventListener('pointermove', function (ev) {
      var rect = renderer.domElement.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      var hits = raycaster.intersectObjects(pickables, false);
      renderer.domElement.style.cursor = hits.length ? 'pointer' : '';
    });

    resize();
    setPose('overview');
    if (loading) {
      loading.textContent = 'Schematic ready';
      setTimeout(function () { loading.classList.add('hidden'); }, 280);
    }

    var clock = 0;
    var last = performance.now();
    function animate(now) {
      requestAnimationFrame(animate);
      var dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      if (!reduceMotion) {
        clock += dt;
        rollers.forEach(function (spin, i) {
          spin.rotation.z += dt * (i === 0 ? 1.4 : -1.4);
        });
        if (coreMesh) {
          var pulse = 1 + Math.sin(clock * 2.2) * 0.05;
          coreMesh.scale.setScalar(pulse);
          matCore.emissiveIntensity = 0.35 + Math.sin(clock * 2.2) * 0.18;
        }
        if (airSpin) airSpin.rotation.z += dt * 0.6;
      }
      controls.update();
      renderer.render(scene, camera);
    }
    requestAnimationFrame(animate);

    api = { resize: resize, focusHotspot: focusHotspot };
    window.addEventListener('resize', resize);
    window.addEventListener('orientationchange', function () {
      setTimeout(resize, 80);
      setTimeout(resize, 250);
    });
    if (typeof ResizeObserver === 'function') {
      var observer = new ResizeObserver(function () { resize(); });
      observer.observe(wrap);
    }
    requestAnimationFrame(function () { resize(); requestAnimationFrame(resize); });
  }

  initChrome();

  if (!window.MeadowlarkThree) {
    showBootError('Need /insect/three-stack.js so the schematic can load Three.js.');
    return;
  }
  MeadowlarkThree.load({ vendorBase: '/insect/vendor', label: 'LitterSoil' }).then(function (stack) {
    boot(stack.THREE, stack.OrbitControls);
  }).catch(function (err) {
    showBootError(err && err.message ? err.message : String(err));
  });
})();
