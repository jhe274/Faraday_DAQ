for i in np.arange(0, 2, self.t_mea):
                # Start the measurement
                start_time = dt.now()
                task.write(self.rise)
                print(f"Timestamp at trigger measurement: {start_time}")

                # Wait for the measurment
                t.sleep(self.t_mea)
                task.write(self.fall)

                # Stop the measurement
                end_time = dt.now()
                
                # self.mod.halt_buffer()
                # self.l2f.halt_buffer()
                # self.dc.halt_buffer()
                # self.b.buffer('CLOS')
                print(f"Timestamp at halt measurement: {end_time}")

                i = i + 1