// src/providers/findings_provider.ts
import * as vscode from "vscode";

export class FindingItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly severity: string,
        public readonly message: string,
        public readonly fix?: string,
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);

        const icons: Record<string, string> = {
            CRITICAL: "$(error)",
            HIGH:     "$(warning)",
            WARNING:  "$(warning)",
            MEDIUM:   "$(info)",
            LOW:      "$(info)",
            INFO:     "$(circle-outline)",
        };

        this.description  = severity;
        this.tooltip      = new vscode.MarkdownString(`**${severity}**\n\n${message}${fix ? `\n\n\`\`\`\n${fix}\n\`\`\`` : ""}`);
        this.iconPath     = new vscode.ThemeIcon(
            severity === "CRITICAL" || severity === "HIGH" ? "error" :
            severity === "WARNING"  || severity === "MEDIUM" ? "warning" : "info"
        );
        this.contextValue = "finding";
    }
}

export class FindingsProvider implements vscode.TreeDataProvider<FindingItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private _items: FindingItem[] = [];

    constructor(private ctx: vscode.ExtensionContext) {}

    updateLogFindings(findings: any[]) {
        this._items = findings.map(f => new FindingItem(
            f.agent?.toUpperCase() || "SECURITY",
            f.severity,
            f.message,
            f.fix_linux || f.fix,
        ));
        this._onDidChangeTreeData.fire();
    }

    updateCodeIssues(issues: any[]) {
        this._items = issues.map(i => new FindingItem(
            `L${i.line || "?"} ${i.rule_id || ""}`,
            i.severity,
            i.message,
            undefined,
        ));
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(el: FindingItem) { return el; }

    getChildren(): FindingItem[] {
        if (this._items.length === 0) {
            return [new FindingItem("No findings yet", "INFO", "Analyze a file to see results.")];
        }
        return this._items;
    }
}
