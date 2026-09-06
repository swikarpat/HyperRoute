export interface IngestAlertPayload {
  account_id: string;
  amount_usd: number;
  sender_country: string;
  receiver_country: string;
  narrative: string;
}

export interface IngestAlertResponse {
  workflow_id: string;
  status: string;
  final_fsm_state: number;
  total_steps_executed: number;
  transaction_amount: number;
  gateway_latency_ms: number;
  circuit_breaker_status: string;
}
