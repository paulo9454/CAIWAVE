import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { demoSession } from "../services/demoApi";

export default function Connecting() {
  const nav = useNavigate();

  useEffect(() => {
    const connect = async () => {
      await demoSession({ user_id: "demo", package: "premium" });
      setTimeout(() => nav("/connected"), 2000);
    };

    connect();
  }, []);

  return <h2>Connecting to network...</h2>;
}
