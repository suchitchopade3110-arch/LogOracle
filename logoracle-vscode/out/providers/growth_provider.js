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
exports.GrowthProvider = exports.GrowthItem = void 0;
const vscode = __importStar(require("vscode"));
class GrowthItem extends vscode.TreeItem {
    constructor(label, value) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.description = value;
    }
}
exports.GrowthItem = GrowthItem;
class GrowthProvider {
    constructor(ctx) {
        this.ctx = ctx;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this._xp = 0;
        this._streak = 0;
        this._badges = [];
    }
    updateXP(xp, streak, badges) {
        this._xp = xp;
        this._streak = streak;
        this._badges = badges;
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(el) { return el; }
    getChildren() {
        return [
            new GrowthItem("XP Total", `${this._xp}`),
            new GrowthItem("Streak", `${this._streak} days`),
            new GrowthItem("Badges", this._badges.length > 0 ? this._badges.join(", ") : "None yet"),
            new GrowthItem("Leaderboard", "Run LogOracle: Show Team Leaderboard"),
        ];
    }
}
exports.GrowthProvider = GrowthProvider;
//# sourceMappingURL=growth_provider.js.map