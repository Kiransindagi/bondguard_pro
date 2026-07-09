export const PORTFOLIO_READ = "portfolio:read";
export const PORTFOLIO_WRITE = "portfolio:write";
export const RISK_READ = "risk:read";
export const RISK_EXECUTE = "risk:execute";
export const STRESS_EXECUTE = "stress:execute";
export const LIQUIDITY_EXECUTE = "liquidity:execute";
export const BREACH_ACKNOWLEDGE = "breach:acknowledge";
export const LIMIT_MANAGE = "limit:manage";
export const PIPELINE_RUN = "pipeline:run";
export const QUALITY_RUN = "quality:run";
export const ANALYTICS_RUN = "analytics:run";
export const REPORT_GENERATE = "report:generate";
export const AUDIT_READ = "audit:read";
export const USER_MANAGE = "user:manage";

export type Permission = string;

export function hasPermission(userPermissions: string[], required: Permission): boolean {
  return userPermissions.includes(required);
}
