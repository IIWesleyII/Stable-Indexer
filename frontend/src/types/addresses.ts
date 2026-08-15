export interface AddressSummary {
  address: string;
  transfer_count: number;
  sent_count: number;
  received_count: number;
  sent_volume: string;
  received_volume: string;
  net_flow: string;
  unique_partners: number;
  first_activity: string;
  last_activity: string;
}

export interface AddressPartner {
  address: string;
  transfer_count: number;
  sent_count: number;
  received_count: number;
  sent_volume: string;
  received_volume: string;
  activity_volume: string;
}

export interface AddressActivity {
  transaction_hash: string;
  log_index: number;
  block_number: number;
  timestamp: string;
  direction: "sent" | "received" | "self";
  counterparty: string;
  amount: string;
  token_symbol: string;
  chain: string;
}

export type PartnerSort = "transfer_count" | "volume";