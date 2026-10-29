# Polyglot Stack Guide: Ruby

This manual details toolchains, test scaffolding, and database isolation for Ruby.

## 1. Detection Markers
- `Gemfile`, `Gemfile.lock`, `*.gemspec`, `Rakefile`

## 2. Standard Commands
- **Targeted Test**: `bundle exec rspec <spec_file>` or `bundle exec rake test TEST=<test_file>`
- **Format / Lint**: `bundle exec rubocop -a` (check: `bundle exec rubocop`)

## 3. Boilerplate Test Scaffolding
If no test exists, create `spec/smoke_spec.rb`:
```ruby
# frozen_string_literal: true

require 'rspec'

RSpec.describe 'Smoke Test Harness' do
  it 'executes cleanly' do
    expect(true).to be true
  end
end
```

## 4. Test Database Isolation
1. Verify that `RAILS_ENV=test` or `RACK_ENV=test` is exported before test execution.
2. Use `database_cleaner` with transaction strategy (`DatabaseCleaner.strategy = :transaction`) to roll back all database mutations.
3. Stub external HTTP calls using `webmock` or `vcr`.
