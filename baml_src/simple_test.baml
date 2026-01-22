class SimpleEvent {
  id string
  summary string
}

function SimpleTest() -> SimpleEvent {
  client "openai/gpt-4o-mini"
  
  prompt #"
    Create a simple event with id and summary.
  "#
}
