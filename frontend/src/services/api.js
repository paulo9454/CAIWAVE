const BASE_URL = "http://localhost:8000"; // change if backend runs elsewhere

export const loginUser = async (username, password) => {
  try {
    const response = await fetch(`${BASE_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Login error:", error);
    return { error: "Server error" };
  }
};
