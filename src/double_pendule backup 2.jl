### A Pluto.jl notebook ###
# v0.20.21

using Markdown
using InteractiveUtils

# ╔═╡ d18ccc66-f563-11f0-9659-8d2b032f54c9
using Plots, CSV, DataFrames

# ╔═╡ 22542c72-57dc-427e-ad1a-7bd43094a2fe
# Karel Vilém Svoboda
# Computational physics 1
# 19.01.2026

# ╔═╡ 4fc0477b-2559-4729-af08-977ce9918ab7
begin

# Mesuré
L1, L2 = 0.09174, 0.06933

# Estimé
m1, m2 = 0.100, 0.03
diam_masse = 0.028
diam_tiges = 0.0015

# Surfaces aérodynamiques projetées
A_masse = π * (diam_masse/2)^2
A_tige1 = (diam_tiges * L1)*2 # 2 tiges
A_tige2 = diam_tiges * L2

# Coefficients de traînée
Cd_disque = 1.1
Cd_cylindre = 1.2

# Constantes
g = 9.81
ρ_air = 1.225

# Coeficients de force quadratique
k1 = 1/2 * ρ_air * (Cd_disque * A_masse + Cd_cylindre * A_tige1)
k2 = 1/2 * ρ_air * (Cd_disque * A_masse + Cd_cylindre * A_tige2)

# Coeficients de décéleration angulaires
b_eff1 = (k1 * L1) / m1
b_eff2 = (k2 * L2) / m2

# Angles initiaux
θ1, θ2 = π, π-0.01
# Vitesse angulaire intiale
ω1, ω2 = 0.0, 0.0

# Constantes de simulation
dt = 0.0005
t_max = 10.0

steps = Int(t_max/dt)
end

# ╔═╡ 1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p
# Charger les données expérimentales
begin
	data_exp = CSV.read("positions.csv", DataFrame)
	
	# Extraire les positions expérimentales de m2
	x2_exp = Float64[]
	y2_exp = Float64[]
	
	for i in 1:nrow(data_exp)
		# Récupérer les données
		cx, cy = data_exp[i, :center_x], data_exp[i, :center_y]
		t1 = data_exp[i, :t1]
		m1x, m1y = data_exp[i, :m1_x], data_exp[i, :m1_y]
		t2 = data_exp[i, :t2]
		m2x, m2y = data_exp[i, :m2_x], data_exp[i, :m2_y]
		
		# Convertir en coordonnées relatives au centre
		# (supposant que le centre est à l'origine dans la simulation)
		push!(x2_exp, (m2x - cx) / 1000)  # Conversion pixels -> mètres (ajuster le facteur)
		push!(y2_exp, -(m2y - cy) / 1000)  # Inverser y et convertir
	end
end

# ╔═╡ 9f0d10ff-c57d-46cd-a03a-e3d1c16925ce
begin
	θ1_old, θ2_old = Float64[], Float64[]
	x1_old, y1_old = Float64[], Float64[]
	x2_old, y2_old = Float64[], Float64[]
end

# ╔═╡ 3cdb4c97-1ad8-40c0-a82c-1a7823d3ff7f
function euler_step(θ1, θ2, ω1, ω2, dt)

	# Angles entre les deux tiges
    Δθ = θ1 - θ2

	# Inertie effective des deux pendules
    denom1 = L1 * (2m1 + m2 - m2*cos(2Δθ))
    denom2 = L2 * (2m1 + m2 - m2*cos(2Δθ))

	# Accélération angulaire du premier bras
    α1 = (
		# Couple gravitationnel
		-g*(2m1 + m2)*sin(θ1)
		# Gravité projetée du second bras
		-m2*g*sin(θ1 - 2θ2)
		# Couplage inertiel
		-2sin(Δθ)*m2*(ω2^2*L2+ω1^2*L1*cos(Δθ))
		# Frottement aérodynamique
		- b_eff1 * ω1 * abs(ω1)) / denom1
	
	# Accélération angulaire du second bras
    α2 = (
		2sin(Δθ)*(
			# couplage inertiel du premier bras
			ω1^2*L1*(m1 + m2)
			# Gravité projectée du premier bras
			+g*(m1+m2)*cos(θ1)
			# Résistance inertielle du bras à sa propre retation
			+ω2^2*L2*m2*cos(Δθ)
			)-b_eff2 * ω2*abs(ω2)) / denom2

	# Euler
	# Nouvelles vitesses angulaires
    ω1_new = ω1 + α1 * dt
    ω2_new = ω2 + α2 * dt

	# Nouvelles positions angulaires
    θ1_new = θ1 + ω1_new * dt
    θ2_new = θ2 + ω2_new * dt

    return θ1_new, θ2_new, ω1_new, ω2_new
end


# ╔═╡ da1cb401-9a5c-4264-bdf9-f0b2f761d129
for i in 1:steps
    θ1, θ2, ω1, ω2 = euler_step(θ1, θ2, ω1, ω2, dt)
    if i % 50 == 0
        push!(θ1_old, θ1)
        push!(θ2_old, θ2)

        x1 = L1 * sin(θ1)
        y1 = -L1 * cos(θ1)

        x2 = x1 + L2 * sin(θ2)
        y2 = y1 - L2 * cos(θ2)

        push!(x1_old, x1)
        push!(y1_old, y1)
        push!(x2_old, x2)
        push!(y2_old, y2)
    end
end

# ╔═╡ 57ca971c-264b-4512-b928-d9b0f08f700c
begin
    @gif for i in 1:length(x1_old)
        plot(
            [0, x1_old[i], x2_old[i]],
            [0, y1_old[i], y2_old[i]],
            marker = :circle,
            ms = [0, 10, 10],
            lw = 2,
            legend = :topright,
            xlim = (-0.2, 0.2),
            ylim = (-0.2, 0.05),
            aspect_ratio = :equal,
            title = "Double Pendule",
            xlabel = "x [m]",
            ylabel = "y [m]",
            color = :red,
            markercolor = :red,
            label = "Simulation"
        )

		# Tracer la trajectoire de la simulation
        plot!(
            x2_old[max(1, i-100):i],
            y2_old[max(1, i-100):i],
            lw = 0.5,
            color = :red,
            alpha = 0.5,
            label = ""
        )
		
		# Tracer les données expérimentales (si disponibles pour cette frame)
		if i <= length(x2_exp)
			plot!(
				x2_exp[1:i],
				y2_exp[1:i],
				lw = 1,
				color = :green,
				alpha = 0.7,
				label = "Expérimental"
			)
		end
    end fps = 60
end