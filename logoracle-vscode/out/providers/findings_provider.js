"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.FindingsProvider = exports.FindingItem = void 0;
// src/providers/findings_provider.ts
const vscode = __importStar(require("vscode"));
class FindingItem extends vscode.TreeItem {
    constructor(label, severity, message, fix) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.label = label;
        this.severity = severity;
        this.message = message;
        this.fix = fix;
        const icons = {
            CRITICAL: "$(error)",
            HIGH: "$(warning)",
            WARNING: "$(warning)",
            MEDIUM: "$(info)",
            LOW: "$(info)",
            INFO: "$(circle-outline)",
        };
        this.description = severity;
        this.tooltip = new vscode.MarkdownString(`**${severity}**\n\n${message}${fix ? `\n\n\`\`\`\n${fix}\n\`\`\`` : ""}`);
        this.iconPath = new vscode.ThemeIcon(severity === "CRITICAL" || severity === "HIGH" ? "error" :
            severity === "WARNING" || severity === "MEDIUM" ? "warning" : "info");
        this.contextValue = "finding";
    }
}
exports.FindingItem = FindingItem;
class FindingsProvider {
    constructor(ctx) {
        this.ctx = ctx;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this._items = [];
    }
    updateLogFindings(findings) {
        this._items = findings.map(f => new FindingItem(f.agent?.toUpperCase() || "SECURITY", f.severity, f.message, f.fix_linux || f.fix));
        this._onDidChangeTreeData.fire();
    }
    updateCodeIssues(issues) {
        this._items = issues.map(i => new FindingItem(`L${i.line || "?"} ${i.rule_id || ""}`, i.severity, i.message, undefined));
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(el) { return el; }
    getChildren() {
        if (this._items.length === 0) {
            return [new FindingItem("No findings yet", "INFO", "Analyze a file to see results.")];
        }
        return this._items;
    }
}
exports.FindingsProvider = FindingsProvider;
//# sourceMappingURL=findings_provider.js.map