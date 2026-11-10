function Login() {
  return (
    <div style={{ padding: "30px" }}>
      <h1>Login</h1>

      <input
        type="email"
        placeholder="Email"
      />

      <br /><br />

      <input
        type="password"
        placeholder="Password"
      />

      <br /><br />

      <button>Login</button>
    </div>
  );
}

export default Login;