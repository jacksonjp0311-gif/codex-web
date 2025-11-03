# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
# Requires -Module Pester -MinimumVersion 5.0
Import-Module "$PSScriptRoot/../../src/Codex.Parser.psm1" -Force

Describe "Parse-CodexDsl" {

  Context "CleanLedger directive" {
    It "parses a CleanLedger step correctly" {
      $lines = @('CleanLedger "path/to/ledger.json"')
      $steps = Parse-CodexDsl -Lines $lines
      $steps.Count        | Should -Be 1
      $steps[0].Type      | Should -Be 'CleanLedger'
      $steps[0].Path      | Should -Be 'path/to/ledger.json'
    }

    It "skips blank lines and comments" {
      $lines = @(
        '# ignore this'
        ''
        'CleanLedger "a.json"'
      )
      $steps = Parse-CodexDsl -Lines $lines
      $steps.Count        | Should -Be 1
      $steps[0].Path      | Should -Be 'a.json'
    }
  }

  Context "Snapshot directive" {
    It "parses Snapshot src and dest" {
      $lines = @('Snapshot "in.json", "outDir"')
      $s = (Parse-CodexDsl -Lines $lines)[0]
      $s.Type             | Should -Be 'Snapshot'
      $s.Src              | Should -Be 'in.json'
      $s.Dest             | Should -Be 'outDir'
    }

    It "throws on malformed Snapshot" {
      $lines = @('Snapshot "onlyOneArg"')
      { Parse-CodexDsl -Lines $lines } | Should -Throw -ErrorMessage '*Snapshot*'
    }
  }

  Context "Validate directive" {
    It "parses Validate script path" {
      $lines = @('Validate "test\Validate.ps1"')
      $v = (Parse-CodexDsl -Lines $lines)[0]
      $v.Type             | Should -Be 'Validate'
      $v.Script           | Should -Be 'test\Validate.ps1'
    }
  }

  Context "Handshake block" {
    It "parses a valid Handshake block" {
      $lines = @(
        'Handshake {'
        '  script = "c.ps1"'
        '  ledger = "l.json"'
        '  output = "o.json"'
        '}'
      )
      $h = (Parse-CodexDsl -Lines $lines)[0]
      $h.Type             | Should -Be 'Handshake'
      $h.Params.script    | Should -Be 'c.ps1'
      $h.Params.ledger    | Should -Be 'l.json'
      $h.Params.output    | Should -Be 'o.json'
    }

    It "throws if Handshake block not closed" {
      $lines = @('Handshake {','  script = "x.ps1"')
      { Parse-CodexDsl -Lines $lines } | Should -Throw -ErrorMessage '*not closed*'
    }

    It "throws on missing Handshake keys" {
      $lines = @('Handshake {','  script = "x.ps1"','}')
      { Parse-CodexDsl -Lines $lines } | Should -Throw -ErrorMessage '*Missing Handshake key*'
    }
  }

  Context "Unknown directives" {
    It "throws on any unrecognized line" {
      $lines = @('FooBar "x"')
      { Parse-CodexDsl -Lines $lines } | Should -Throw -ErrorMessage '*Unrecognized DSL line*'
    }
  }

}

