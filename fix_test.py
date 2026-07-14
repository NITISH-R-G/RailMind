with open("frontend/src/components/LiveMap.test.jsx", "r") as f:
    content = f.read()

# Update the test to use a reroute_plan that is parseable by the new parsing logic
old_test_plan = """      {
        id: "inc1",
        train_number: "99999",
        severity: "critical",
        approved: true,
        reroute_plan: "Test Reroute"
      }"""

new_test_plan = """      {
        id: "inc1",
        train_number: "99999",
        severity: "critical",
        approved: true,
        reroute_plan: "NDLS ➔ ALD"
      }"""

content = content.replace(old_test_plan, new_test_plan)

with open("frontend/src/components/LiveMap.test.jsx", "w") as f:
    f.write(content)
