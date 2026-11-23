export const metadata = {
  title: "Prompt-Based Video Editing Engine",
  description: "Natural-language video editing: upload, prompt, frame-accurate cut.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
