= Financial Statements for AY {{cfg.fy+1}}
:toc:
:toc-title: Reports

// Each sub-report below is a standalone document (its own top-level
// '= Title'). include::[leveloffset=+N] demotes that title into a proper
// section instead of a second document title, so `asciidoctor-pdf
// index.adoc` (or plain `asciidoctor index.adoc` for HTML) produces one
// single combined document containing everything, with no file-to-file
// links needed at all.

== Cashbooks

{% for j in reports.journal %}
include::{{j}}[leveloffset=+2]

{% endfor %}
{% for j in reports.depreciation %}
include::{{j}}[leveloffset=+1]

{% endfor %}
{% for j in reports.balance_sheet %}
include::{{j}}[leveloffset=+1]

{% endfor %}
{% for j in reports.pnl %}
include::{{j}}[leveloffset=+1]

{% endfor %}
{% for j in reports.gst %}
include::{{j}}[leveloffset=+1]

{% endfor %}
