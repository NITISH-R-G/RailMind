const { performance } = require('perf_hooks');

const incidents = Array.from({ length: 10000 }, (_, i) => ({
  id: i,
  severity: 'info',
  timestamp: '12:00',
  title: `Incident ${i}`
}));

function benchmark() {
  const iterations = 1000000;

  // Method 1: slice + map
  const start1 = performance.now();
  let dummy1 = 0;
  for (let i = 0; i < iterations; i++) {
    const res = incidents.slice(0, 5).map(inc => {
      return { id: inc.id, severity: inc.severity, title: inc.title };
    });
    dummy1 += res.length;
  }
  const end1 = performance.now();

  // Method 2: loop
  const start2 = performance.now();
  let dummy2 = 0;
  for (let i = 0; i < iterations; i++) {
    const len = Math.min(5, incidents.length);
    const res = new Array(len);
    for(let j=0; j<len; j++) {
      const inc = incidents[j];
      res[j] = { id: inc.id, severity: inc.severity, title: inc.title };
    }
    dummy2 += res.length;
  }
  const end2 = performance.now();

  console.log(`Method 1 (slice+map): ${(end1 - start1).toFixed(2)} ms`);
  console.log(`Method 2 (loop): ${(end2 - start2).toFixed(2)} ms`);
}

benchmark();
