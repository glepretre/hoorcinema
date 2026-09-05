import { useQuery } from "@tanstack/react-query";
import { Alert, Spin, Typography } from "antd";

import { getHello } from "./api/hello";

const { Title } = Typography;

export default function App() {
  const helloQuery = useQuery({
    queryKey: ["hello"],
    queryFn: getHello,
  });

  return (
    <main className="page-shell">
      <section className="hero" aria-labelledby="page-title">
        <Title id="page-title">Hoorcinema</Title>
        <div className="hello-output" aria-live="polite">
          {helloQuery.isPending && <Spin size="small" />}
          {helloQuery.isError && (
            <Alert
              type="error"
              showIcon
              message="Connection failed"
              description={helloQuery.error.message}
            />
          )}
          {helloQuery.data && (
            <Title level={2} className="hello-message">
              {helloQuery.data.message}
            </Title>
          )}
        </div>
      </section>
    </main>
  );
}
