# Test na żywo: tokeny + poprawność na nowych stronach i scenariusze (klik, wyszukiwanie, back, robots, SSRF, 404).
# Uruchomienie: powershell -File tests\bench\sprawdz.ps1 -Komenda <exe> [-Argumenty "..."]
param(
    [Parameter(Mandatory)] [string]$Komenda,
    [string]$Argumenty = '',
    [int]$Zestaw = 1
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

# Strony: selektor do extract i minimalna oczekiwana liczba wyników (poprawność)
$strony = @(
    @{ nazwa = 'Wikipedia EN';   url = 'https://en.wikipedia.org/wiki/Poland';                       sel = '#mw-content-text h2'; min = 8 },
    @{ nazwa = 'MDN docs';       url = 'https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/table'; sel = 'h2'; min = 4 },
    @{ nazwa = 'Rust std docs';  url = 'https://doc.rust-lang.org/std/vec/struct.Vec.html';          sel = 'h2'; min = 3 },
    @{ nazwa = 'PyPI paczka';    url = 'https://pypi.org/project/httpx/';                            sel = 'h1'; min = 1 },
    @{ nazwa = 'gov.pl';         url = 'https://www.gov.pl/web/gov';                                 sel = 'a[href]'; attr = 'href'; min = 10 },
    @{ nazwa = 'Hacker News new';url = 'https://news.ycombinator.com/newest';                        sel = '.titleline > a'; min = 20 },
    @{ nazwa = 'Sklep (scrape)'; url = 'https://webscraper.io/test-sites/e-commerce/allinone';       sel = '.thumbnail .price'; min = 3 },
    @{ nazwa = 'Tabela (scrape)';url = 'https://www.scrapethissite.com/pages/simple/';               sel = '.country-name'; min = 200 }
)

# Zestaw 2: newsy PL, sklepy, dokumentacja, forum, blog, kodowanie, strona SPA (oczekiwane ograniczenie)
$zestaw2 = @(
    @{ nazwa = 'Newsy PL (PAP)';   url = 'https://www.pap.pl/';                                   sel = 'h2, h3'; min = 10 },
    @{ nazwa = 'Wikipedia PL';     url = 'https://pl.wikipedia.org/wiki/Warszawa';                sel = '#mw-content-text h2'; min = 8 },
    @{ nazwa = 'Sklep (scrape 2)'; url = 'https://webscraper.io/test-sites/e-commerce/static/computers/laptops'; sel = '.thumbnail .title'; attr = 'title'; min = 6 },
    @{ nazwa = 'Docs Django';      url = 'https://docs.djangoproject.com/en/stable/topics/http/urls/'; sel = 'h2'; min = 5 },
    @{ nazwa = 'Forum (Discourse)';url = 'https://discuss.python.org/latest';                     sel = 'a.title'; min = 10 },
    @{ nazwa = 'Blog (Rust)';      url = 'https://blog.rust-lang.org/';                           sel = 'a[href*="/20"]'; attr = 'href'; min = 10 },
    @{ nazwa = 'Kodowanie ISO-8859-2'; url = 'https://www.ietf.org/rfc/rfc2616.txt';              sel = 'body'; min = 1 },
    @{ nazwa = 'Tabela (XE kursy)';url = 'https://www.x-rates.com/table/?from=PLN&amount=1';      sel = 'table.tablesorter td:first-child'; min = 10 },
    @{ nazwa = 'SPA (React docs)'; url = 'https://react.dev/learn';                               sel = 'h1, h2'; min = 2 }
)
if ($Zestaw -eq 2) { $strony = $zestaw2 }

function Tokeny([string]$s) { [math]::Ceiling($s.Length / 4) }

$psi = New-Object Diagnostics.ProcessStartInfo $Komenda, $Argumenty
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = [Text.Encoding]::UTF8
$proc = [Diagnostics.Process]::Start($psi)
$wejscie = New-Object IO.StreamWriter($proc.StandardInput.BaseStream, (New-Object Text.UTF8Encoding $false))
$script:id = 0

function Wywolaj($narzedzie, $argumenty) {
    $script:id++
    $z = @{ jsonrpc = '2.0'; id = $script:id; method = 'tools/call'; params = @{ name = $narzedzie; arguments = $argumenty } } | ConvertTo-Json -Compress -Depth 5
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $wejscie.WriteLine($z); $wejscie.Flush()
    $odp = $proc.StandardOutput.ReadLine() | ConvertFrom-Json
    [pscustomobject]@{ tekst = [string]$odp.result.content[0].text; blad = [bool]$odp.result.isError; ms = $sw.ElapsedMilliseconds }
}

# Numer [ref] pierwszej linii migawki pasującej do wzorca
function Ref($migawka, $wzorzec) {
    $l = ($migawka -split "`n") | Where-Object { $_ -match $wzorzec } | Select-Object -First 1
    if ($l -match '^\[(\d+)\]') { [int]$Matches[1] } else { 0 }
}

# --- Tokeny i poprawność ekstrakcji ---
$tabela = foreach ($s in $strony) {
    try { $html = (Invoke-WebRequest $s.url -UseBasicParsing -UserAgent 'Mozilla/5.0').Content } catch { $html = '' }
    $nav = Wywolaj 'navigate' @{ url = $s.url }
    if ($nav.blad) { [pscustomobject]@{ Strona = $s.nazwa; Wynik = 'BLAD: ' + $nav.tekst.Substring(0, [math]::Min(90, $nav.tekst.Length)) }; continue }
    $read = Wywolaj 'read' @{ max_chars = 1000000 }
    $ext = Wywolaj 'extract' @{ selector = $s.sel; attr = $s.attr; max_chars = 1000000 }
    $linie = ($ext.tekst -split "`n").Count - 1
    $ekrany = [math]::Max(1, [math]::Ceiling($read.tekst.Length / 2500))
    [pscustomobject]@{
        Strona        = $s.nazwa
        'HTML tok'    = Tokeny $html
        'snap tok'    = Tokeny $nav.tekst
        'read tok'    = Tokeny $read.tekst
        'extr tok'    = Tokeny $ext.tekst
        'zrzuty tok'  = $ekrany * 1365
        'extr wyn.'   = $linie
        'nav ms'      = $nav.ms
        Wynik         = if ($linie -ge $s.min -and $read.tekst.Length -gt 200) { 'OK' } else { "ZLE (min $($s.min), read $($read.tekst.Length) zn.)" }
    }
}

# --- Scenariusze ---
$scen = [Collections.Generic.List[object]]::new()
function Wynik($nazwa, $ok, $szczegol) { $scen.Add([pscustomobject]@{ Scenariusz = $nazwa; Wynik = if ($ok) { 'OK' } else { 'ZLE' }; Szczegol = $szczegol }) }

$n = Wywolaj 'navigate' @{ url = 'https://quotes.toscrape.com/' }
$nr = Ref $n.tekst 'link "Next'
$k = Wywolaj 'click' @{ ref = $nr }
Wynik 'click: link Next (paginacja)' ($k.tekst -match 'quotes.toscrape.com/page/2/') "ref=$nr"

$b = Wywolaj 'back' @{}
Wynik 'back: powrót do strony 1' ($b.tekst -match 'quotes.toscrape.com/ ') ''

$n = Wywolaj 'navigate' @{ url = 'https://en.wikipedia.org/wiki/Main_Page' }
$nr = Ref $n.tekst 'name=search'
$t = Wywolaj 'type' @{ ref = $nr; text = 'Rust programming language'; submit = $true }
# Wikipedia zabrania automatom /w/ w robots.txt – oczekiwana odmowa, ale z poprawnie złożonym URL formularza
Wynik 'type+submit: formularz GET (+robots /w/)' ($t.tekst -match 'search=Rust\+programming\+language') ($t.tekst -split "`n")[0]

$e = Wywolaj 'extract' @{ selector = '[[[' }
Wynik 'extract: zły selektor = błąd' $e.blad ''

$r = Wywolaj 'navigate' @{ url = 'https://www.reddit.com/r/rust/' }
Wynik 'robots.txt: blokada' ($r.blad -and $r.tekst -match 'robots') ($r.tekst -split "`n")[0]

$l = Wywolaj 'navigate' @{ url = 'http://localhost:8080/' }
Wynik 'SSRF: localhost zablokowany' ($l.blad -and $l.tekst -match 'prywatnej') ''

$m = Wywolaj 'navigate' @{ url = 'http://169.254.169.254/latest/meta-data/' }
Wynik 'SSRF: metadane chmury 169.254.169.254' ($m.blad -and $m.tekst -match 'prywatnej') ''

$x = Wywolaj 'navigate' @{ url = 'https://httpbin.org/status/404' }
Wynik 'HTTP 404 = błąd' ($x.blad -and $x.tekst -match '404') ''

$p = Wywolaj 'navigate' @{ url = 'https://httpbin.org/image/png' }
Wynik 'obraz zamiast strony = błąd' ($p.blad -and $p.tekst -match 'tekstowa') ''

$rd = Wywolaj 'navigate' @{ url = 'https://httpbin.org/redirect/3' }
Wynik 'przekierowania x3 (cel JSON)' (-not $rd.blad -and $rd.tekst -match 'httpbin.org/get') ($rd.tekst -split "`n")[0]

$proc.Refresh()
$pamiec = $proc.PeakWorkingSet64
$wejscie.Close()
$proc.WaitForExit(5000) | Out-Null

$tabela | Format-Table -AutoSize | Out-String -Width 300
$scen | Format-Table -AutoSize | Out-String -Width 300
"Szczytowa pamiec: {0:N1} MB" -f ($pamiec / 1MB)
