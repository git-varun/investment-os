from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table


class PortfolioTUI:
    def __init__(self):
        self.console = Console()

    def generate_layout(self, assets, total_val, briefing, health_report) -> Layout:  # <-- Accept health_report
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=5)  # <-- Made footer bigger
        )

        # 2. Header & Footer
        layout["header"].update(Panel(
            f"🚀 INVESTMENT OS v2.0 | LIVE TERMINAL | {datetime.now().strftime('%X')}",
            style="bold white on blue"
        ))
        layout["footer"].update(Panel(
            f"💰 TOTAL NET WORTH: ₹{total_val:,.2f}",
            style="bold green", border_style="bright_green"
        ))

        # 3. Main Table Update (SORT BY VALUE)
        table = Table(expand=True, border_style="dim")
        table.add_column("Asset", style="cyan")
        table.add_column("Qty", justify="right")
        table.add_column("Value (INR)", justify="right", style="green")
        table.add_column("Math Signal", style="bold yellow")
        table.add_column("RSI", justify="right")
        table.add_column("Trailing SL", justify="right", style="red")

        # SORT ASSETS DESCENDING BY VALUE so your biggest holdings are always on screen
        sorted_assets = sorted(assets, key=lambda x: x.get('value_inr', 0), reverse=True)

        for a in sorted_assets:
            signal = a.get('math_signal', 'HOLD')
            rsi = str(a.get('rsi', '-'))
            tsl = f"₹{a.get('tsl', 0):,.2f}" if a.get('tsl') else "-"

            if "PROFIT" in signal or "SELL" in signal:
                signal_str = f"[bold red]{signal}[/bold red]"
            elif "AVG" in signal:
                signal_str = f"[bold green]{signal}[/bold green]"
            else:
                signal_str = f"[dim]{signal}[/dim]"

            table.add_row(
                a['symbol'], f"{a['qty']:.4f}", f"₹{a.get('value_inr', 0):,.2f}",
                signal_str, rsi, tsl
            )

        # 4. AI Insight Panel (Upgraded for Deeper Intel)
        if not briefing:
            ai_content = "[dim]Waiting for intelligence cycle...[/dim]"
        else:
            vibe_color = "green" if briefing.get('global_score', 0) > 0 else "red"
            ai_content = f"[bold {vibe_color}]Vibe:[/bold {vibe_color}] {briefing.get('market_vibe', 'N/A')}\n\n"

            # ADD THE NEW MACRO ANALYSIS
            if briefing.get('macro_analysis'):
                ai_content += f"[italic dim]{briefing.get('macro_analysis')}[/italic dim]\n\n"

            directives = briefing.get('directives', [])
            if directives:
                ai_content += "[bold cyan]🎯 STRATEGIC DIRECTIVES:[/bold cyan]\n"
                for d in directives:
                    # Defensive check: Did the AI output a string instead of a dict?
                    if not isinstance(d, dict):
                        ai_content += f"\n• [bold]Alert[/bold] -> [dim]{d}[/dim]\n"
                        continue

                    sym = d.get('symbol', 'UNK')
                    act = d.get('action', 'HOLD').upper()
                    rsn = d.get('reasoning', '')

                    if "BUY" in act or "AVG" in act:
                        act_str = f"[bold green bg_black] {act} [/]"
                    elif "SELL" in act or "CUT" in act:
                        act_str = f"[bold white bg_red] {act}[/]"
                    else:
                        act_str = f"[bold yellow bg_black] {act} [/]"

                    ai_content += f"\n• [bold]{sym}[/bold] -> {act_str}\n  [dim]{rsn}[/dim]\n"

        layout["body"].split_row(
            Layout(Panel(table, title="📊 Portfolio")),
            Layout(Panel(ai_content, title="🧠 AI Alpha Brain", border_style="yellow"))
        )

        # 5. Build Macro Risk Footer
        alloc_str = " | ".join([f"{k}: {v}%" for k, v in health_report.get('allocation', {}).items()])
        beta = health_report.get('beta', 1.0)

        # Color code beta (Red if hyper-volatile, Green if stable)
        beta_color = "red" if beta > 1.2 else "green" if beta < 0.8 else "yellow"

        risk_text = f"[bold]Asset Allocation:[/bold] {alloc_str}\n"
        risk_text += f"[bold]Portfolio Beta:[/bold] [{beta_color}]{beta}[/{beta_color}] (1.0 = Nifty 50)\n"

        if health_report.get('high_correlation_warning'):
            risk_text += f"⚠️ [bold red]RISK:[/bold red] {health_report['high_correlation_warning']}"
        else:
            risk_text += "✅ [bold green]Diversification Optimal[/bold green]"

        layout["footer"].update(Panel(
            risk_text,
            title="🛡️ Risk & Allocation Profile",
            border_style="bright_blue"
        ))

        return layout
