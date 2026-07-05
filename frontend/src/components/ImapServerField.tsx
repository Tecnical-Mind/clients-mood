
const KNOWN_IMAP_PROVIDERS: Record<string, { server: string; port: number }> = {
  "gmail.com": { server: "imap.gmail.com", port: 993 },
  "googlemail.com": { server: "imap.gmail.com", port: 993 },
  "outlook.com": { server: "outlook.office365.com", port: 993 },
  "hotmail.com": { server: "outlook.office365.com", port: 993 },
  "live.com": { server: "outlook.office365.com", port: 993 },
  "yahoo.com": { server: "imap.mail.yahoo.com", port: 993 },
  "icloud.com": { server: "imap.mail.me.com", port: 993 },
};

export function suggestImapServer(email: string): { server: string; port: number } | null {
  const domain = email.split("@")[1]?.toLowerCase();
  return domain ? KNOWN_IMAP_PROVIDERS[domain] ?? null : null;
}

interface Props {
  server: string;
  port: number;
  onChange: (server: string, port: number) => void;
}

export function ImapServerField({ server, port, onChange }: Props) {
  return (
    <>
      <label htmlFor="imap_server">Servidor IMAP</label>
      <input
        id="imap_server"
        type="text"
        value={server}
        onChange={(e) => onChange(e.target.value, port)}
        placeholder="imap.tu-dominio.com"
        required
      />
      <label htmlFor="imap_port">Puerto IMAP</label>
      <input
        id="imap_port"
        type="number"
        value={port}
        onChange={(e) => onChange(server, Number(e.target.value))}
        required
      />
    </>
  );
}
