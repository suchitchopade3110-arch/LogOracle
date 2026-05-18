import * as vscode from "vscode";

export class GrowthItem extends vscode.TreeItem {
    constructor(label: string, value: string) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.description = value;
    }
}

export class GrowthProvider implements vscode.TreeDataProvider<GrowthItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private _xp = 0;
    private _streak = 0;
    private _badges: string[] = [];

    constructor(private ctx: vscode.ExtensionContext) {}

    updateXP(xp: number, streak: number, badges: string[]) {
        this._xp = xp;
        this._streak = streak;
        this._badges = badges;
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(el: GrowthItem) { return el; }

    getChildren(): GrowthItem[] {
        return [
            new GrowthItem("XP Total", `${this._xp}`),
            new GrowthItem("Streak", `${this._streak} days`),
            new GrowthItem("Badges", this._badges.length > 0 ? this._badges.join(", ") : "None yet"),
            new GrowthItem("Leaderboard", "Run LogOracle: Show Team Leaderboard"),
        ];
    }
}
