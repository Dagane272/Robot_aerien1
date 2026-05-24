clear; clc; close all;
%% =========================
% DIMENSIONS INTERNES (Gardées pour la cohérence visuelle)
%% =========================
largeur = 1000;
hauteur = 2000;
altitude = 160;
v_moy = 30;

% Valeurs textuelles pour l'affichage réel demandé
largeur_aff = 1;
hauteur_aff = 2;
altitude_aff = 0.16;
v_moy_aff = 0.03;

%% =========================
% CHARGEMENT DE LA TEXTURE
%% =========================
scriptDir = fileparts(mfilename('fullpath'));
texturePath = fullfile(scriptDir, 'plante.png');
if ~exist(texturePath, 'file')
    textureImg = uint8(cat(3, zeros(400), ones(400)*150, zeros(400)));
else
    textureImg = imread(texturePath);
end
[imgH, imgW, ~] = size(textureImg);

%% =========================
% AMÉLIORATION QUALITÉ IMAGE
%% =========================
imgDouble = double(textureImg) / 255;
sharpenKernel = fspecial('unsharp', 0.8);
imgSharp = zeros(size(imgDouble));
for c = 1:3
    imgSharp(:,:,c) = imfilter(imgDouble(:,:,c), sharpenKernel, 'replicate');
end
imgSharp = max(0, min(1, imgSharp));
imgHSV = rgb2hsv(imgSharp);
imgHSV(:,:,2) = min(1, imgHSV(:,:,2) * 1.6);
imgHSV(:,:,3) = min(1, imgHSV(:,:,3) * 1.15);
imgVivid = hsv2rgb(imgHSV);
imgVivid(:,:,2) = min(1, imgVivid(:,:,2) * 1.2);
imgVivid(:,:,1) = min(1, imgVivid(:,:,1) * 1.1);
textureEnhanced = uint8(imgVivid * 255);
textureEnhanced = imadjust(textureEnhanced, [0.1 0.9], [0 1]);

%% =========================
% DIMENSIONS PARCELLE + FIGURE
%% =========================
resX = imgW; resY = imgH;
[x, y] = meshgrid(linspace(0, largeur, resX), linspace(0, hauteur, resY));
z = zeros(size(x));

fig = figure('Color', [1 1 1], ...
'Name', sprintf('Planificateur de Trajectoire - %dx%dm | Alt: %.2fm | Vit: %.2fm/s', largeur_aff, hauteur_aff, altitude_aff, v_moy_aff), ...
'NumberTitle', 'off', 'Units', 'normalized', 'OuterPosition', [0 0 1 1]);
ax = axes('Parent', fig, 'Units', 'normalized', 'Position', [0.05 0.1 0.7 0.8]);
hold on;

%% =========================
% TERRAIN + HÉLIPAD + DRONE
%% =========================
base_profondeur = hauteur * 0.3;
[xb, yb] = meshgrid(linspace(0, largeur, 300), linspace(-base_profondeur, 0, 300));
zb = zeros(size(xb));
gazongImg = zeros(300, 300, 3);
for i = 1:300
    for j = 1:300
        bruit = 0.02 * rand();
        gazongImg(i,j,1) = 0.1 + bruit;
        gazongImg(i,j,2) = 0.65 + bruit * 1.2;
        gazongImg(i,j,3) = 0.1 + bruit;
    end
end
gazongImg = uint8(imgaussfilt(gazongImg, 1.5) * 255);
surf(ax, xb, yb, zb, 'CData', gazongImg, 'FaceColor', 'texturemap', 'EdgeColor', 'none', 'FaceLighting', 'none');

plot3(ax, [0 largeur], [-base_profondeur -base_profondeur], [0 0], 'Color', [0.2 0.5 0.2], 'LineWidth', 2);
plot3(ax, [0 0], [-base_profondeur 0], [0 0], 'Color', [0.2 0.5 0.2], 'LineWidth', 2);
plot3(ax, [largeur largeur], [-base_profondeur 0], [0 0], 'Color', [0.2 0.5 0.2], 'LineWidth', 2);

x_base = largeur / 2;
y_base = -base_profondeur / 2;
r_pad = min(largeur, base_profondeur) * 0.2;
theta = linspace(0, 2*pi, 100);
fill3(ax, x_base + r_pad*cos(theta), y_base + r_pad*sin(theta), 0.05*ones(1,100), [1 0.85 0], 'EdgeColor', [0.8 0.6 0], 'LineWidth', 2);
text(ax, x_base, y_base, 0.15, 'H', 'FontSize', 40, 'FontWeight', 'bold', 'Color', [1 0.75 0], 'HorizontalAlignment', 'center');

line(ax, [0 largeur], [0 0], [0 0], 'Color', [0.3 0.3 0.3], 'LineWidth', 2, 'LineStyle', '--');
surf(ax, x, y, z, 'CData', textureEnhanced, 'FaceColor', 'texturemap', 'EdgeColor', 'none', 'PickableParts', 'all');

% Drone
drone_scale = sqrt(largeur^2 + hauteur^2) * 0.04;
L_bras = drone_scale; R_prop = drone_scale * 0.40; R_corps = drone_scale * 0.047;
R_sp = drone_scale * 0.23; R_cam = drone_scale * 0.17;

drone_group = hgtransform('Parent', ax);
set(drone_group, 'Matrix', makehgtform('translate', [x_base, y_base, 5]));
set(ax, 'DataAspectRatio', [1 1 1]);

[xc, yc, zc] = cylinder(R_corps, 20);
surf(zc*2*L_bras - L_bras, yc, xc, 'FaceColor', [1 1 0], 'EdgeColor', 'none', 'Parent', drone_group);
surf(xc, zc*2*L_bras - L_bras, yc, 'FaceColor', [1 1 0], 'EdgeColor', 'none', 'Parent', drone_group);

t_h = linspace(0, 2*pi, 30);
px = R_prop * cos(t_h); py = R_prop * sin(t_h); pz = zeros(size(t_h)) + R_corps*1.2;
fill3(L_bras+px, py, pz, [0.1 0.1 0.1], 'FaceAlpha',0.9,'EdgeColor','none','Parent',drone_group);
fill3(-L_bras+px, py, pz, [0.1 0.1 0.1], 'FaceAlpha',0.9,'EdgeColor','none','Parent',drone_group);
fill3(px, L_bras+py, pz, [0.1 0.1 0.1], 'FaceAlpha',0.9,'EdgeColor','none','Parent',drone_group);
fill3(px, -L_bras+py, pz, [0.1 0.1 0.1], 'FaceAlpha',0.9,'EdgeColor','none','Parent',drone_group);

[X_sp, Y_sp, Z_sp] = sphere(40);
surf(X_sp*R_sp, Y_sp*R_sp, Z_sp*(R_sp*0.5), 'FaceColor',[1 1 0], 'EdgeColor','none','Parent',drone_group);
surf(X_sp*R_cam, Y_sp*R_cam, Z_sp*(R_cam*0.6) + R_sp*0.5, 'FaceColor',[0.3 0.3 0.3],'EdgeColor','none','Parent',drone_group);

vertical_line = line(ax, [x_base x_base], [y_base y_base], [0 5], ...
'Color', [1 0 0], 'LineWidth', 2.5, 'LineStyle', '-');

zlim([0 altitude*3]); grid on; view(40, 35);
xlabel('X (m)'); ylabel('Y (m)'); zlabel('Altitude Z (m)');
xlim([-10 largeur+10]); ylim([-base_profondeur-10 hauteur+10]);

%% ========================================================================
% MODIFICATION DES GRADUATIONS DES AXES (Échelle visuelle 1m x 2m)
% ========================================================================
% On récupère les graduations générées automatiquement par MATLAB
x_ticks = get(ax, 'XTick');
y_ticks = get(ax, 'YTick');
z_ticks = get(ax, 'ZTick');

% On recalcule les étiquettes correspondantes divisées par 1000
set(ax, 'XTickLabel', string(x_ticks / 1000));
set(ax, 'YTickLabel', string(y_ticks / 1000));
set(ax, 'ZTickLabel', string(z_ticks / 1000));

light('Position', [largeur/2 hauteur/2 500], 'Style', 'infinite');
lighting gouraud; material([1.0 1.0 0.05 2]);

%% =========================
% INTERFACE
%% =========================
hWP_temp = plot3(ax, 0, 0, altitude, 'ro', 'MarkerSize', 10, 'MarkerFaceColor', 'r', 'Visible', 'off');
hLine_temp = line(ax, [0 0], [0 0], [0 altitude], 'Color', 'r', 'LineWidth', 1.5, 'LineStyle', '--', 'Visible', 'off');

mode = 'saisie';
setappdata(fig, 'mode', mode);
setappdata(fig, 'allWaypoints', []);
setappdata(fig, 'isDrawing', false);
setappdata(fig, 'hWP_temp', hWP_temp);
setappdata(fig, 'hLine_temp', hLine_temp);
setappdata(fig, 'currentPos', [0, 0]);
setappdata(fig, 'drone_group', drone_group);
setappdata(fig, 'vertical_line', vertical_line);
setappdata(fig, 'x_base', x_base);
setappdata(fig, 'y_base', y_base);
setappdata(fig, 'altitude', altitude);
setappdata(fig, 'v_moy', v_moy);
setappdata(fig, 'largeur', largeur);
setappdata(fig, 'hauteur', hauteur);
setappdata(fig, 'altitude_aff', altitude_aff); % Sauvegarde pour affichage dynamique

pnl = uipanel('Title','Commandes','FontSize',12,'BackgroundColor','white',...
'Units', 'normalized', 'Position',[.78 .35 .18 .50]);

uicontrol('Parent',pnl,'Style','text', ...
'String', sprintf('Terrain : %dx%d m\nAltitude : %.2f m\nVitesse : %.2f m/s', largeur_aff, hauteur_aff, altitude_aff, v_moy_aff), ...
'Units','normalized','Position',[.05 .82 .9 .15], ...
'BackgroundColor',[0.93 0.97 1], 'FontSize', 9, 'ForegroundColor',[0.1 0.1 0.5], ...
'HorizontalAlignment','left');

uicontrol('Parent',pnl,'Style','pushbutton','String','✏️ Mode Saisie Waypoints',...
'Units','normalized','Position',[.05 .65 .9 .13],...
'BackgroundColor',[.2 .7 .2],'ForegroundColor','w','FontWeight','bold',...
'Callback', @(src,ev) setMode(fig, ax, 'saisie'));

uicontrol('Parent',pnl,'Style','pushbutton','String','🔄 Mode Rotation Terrain',...
'Units','normalized','Position',[.05 .50 .9 .13],...
'BackgroundColor',[.2 .4 .7],'ForegroundColor','w','FontWeight','bold',...
'Callback', @(src,ev) setMode(fig, ax, 'rotation'));

uicontrol('Parent',pnl,'Style','pushbutton','String','📌 Fixer Waypoint (OK)',...
'Units','normalized','Position',[.05 .35 .9 .13],...
'BackgroundColor',[.1 .5 .1],'ForegroundColor','w','FontWeight','bold',...
'Callback', @(src,ev) fixWaypoint(fig, ax));

uicontrol('Parent',pnl,'Style','pushbutton','String','✈️ Tracer Trajectoire',...
'Units','normalized','Position',[.05 .20 .9 .13],...
'BackgroundColor',[.1 .1 .5],'ForegroundColor','w','FontWeight','bold',...
'Callback', @(src,ev) drawTrajectory(fig, ax));

modeLabel = uicontrol('Parent',pnl,'Style','text','String','Mode: SAISIE',...
'Units','normalized','Position',[.05 .02 .9 .10],...
'BackgroundColor',[.9 .9 .9],'FontWeight','bold',...
'FontSize',10,'ForegroundColor',[0 0.5 0]);
setappdata(fig, 'modeLabel', modeLabel);

set(fig, 'WindowButtonDownFcn', @startPointing);
set(fig, 'WindowButtonMotionFcn', @updatePointing);
set(fig, 'WindowButtonUpFcn', @stopPointing);

%% ==========================================
% FONCTIONS LOCALES
%% ==========================================
function setMode(fig, ax, newMode)
    setappdata(fig, 'mode', newMode);
    modeLabel = getappdata(fig, 'modeLabel');
    if strcmp(newMode, 'saisie')
        set(modeLabel, 'String', 'Mode: SAISIE', 'ForegroundColor', [0 0.5 0]);
        rotate3d(ax, 'off');
        set(fig, 'WindowButtonDownFcn', @startPointing);
        set(fig, 'WindowButtonMotionFcn', @updatePointing);
        set(fig, 'WindowButtonUpFcn', @stopPointing);
    else
        set(modeLabel, 'String', 'Mode: ROTATION', 'ForegroundColor', [0.5 0 0]);
        hWP = getappdata(fig, 'hWP_temp');
        hLine = getappdata(fig, 'hLine_temp');
        set(hWP, 'Visible', 'off');
        set(hLine, 'Visible', 'off');
        set(fig, 'WindowButtonDownFcn', []);
        set(fig, 'WindowButtonMotionFcn', []);
        set(fig, 'WindowButtonUpFcn', []);
        rotate3d(ax, 'on');
    end
end

function startPointing(src, ~)
    mode = getappdata(src, 'mode');
    if strcmp(mode, 'saisie')
        setappdata(src, 'isDrawing', true);
        updatePointing(src);
    end
end

function updatePointing(src, ~)
    mode = getappdata(src, 'mode');
    if strcmp(mode, 'saisie') && getappdata(src, 'isDrawing')
        ax_h = findobj(src, 'Type', 'axes');
        cp = get(ax_h, 'CurrentPoint');
        p1 = cp(1,:); p2 = cp(2,:);
        t = -p1(3) / (p2(3) - p1(3));
        x_pt = p1(1) + t * (p2(1) - p1(1));
        y_pt = p1(2) + t * (p2(2) - p1(2));
        largeur = getappdata(src, 'largeur');
        hauteur = getappdata(src, 'hauteur');
        x_pt = max(0, min(largeur, x_pt));
        y_pt = max(0, min(hauteur, y_pt));
        setappdata(src, 'currentPos', [x_pt, y_pt]);
        altitude = getappdata(src, 'altitude');
        hWP = getappdata(src, 'hWP_temp'); 
        hLine = getappdata(src, 'hLine_temp'); 
        set(hWP, 'XData', x_pt, 'YData', y_pt, 'ZData', altitude, 'Visible', 'on');
        set(hLine, 'XData', [x_pt x_pt], 'YData', [y_pt y_pt], 'ZData', [0 altitude], 'Visible', 'on');
        drawnow limitrate;
    end
end

function stopPointing(src, ~)
    mode = getappdata(src, 'mode');
    if strcmp(mode, 'saisie')
        setappdata(src, 'isDrawing', false);
    end
end

function fixWaypoint(fig, ax)
    mode = getappdata(fig, 'mode');
    if ~strcmp(mode, 'saisie')
        msgbox('Veuillez passer en Mode Saisie Waypoints pour fixer des points.');
        return;
    end
    pos = getappdata(fig, 'currentPos');
    if pos(1) == 0 && pos(2) == 0
        msgbox('Veuillez cliquer sur la parcelle pour sélectionner un point.');
        return;
    end
    altitude = getappdata(fig, 'altitude');
    wps = getappdata(fig, 'allWaypoints');
    wps = [wps; pos];
    setappdata(fig, 'allWaypoints', wps);
    plot3(ax, pos(1), pos(2), altitude, 'bo', 'MarkerSize', 10, 'MarkerFaceColor', 'b', 'MarkerEdgeColor', 'w');
    line(ax, [pos(1) pos(1)], [pos(2) pos(2)], [0 altitude], 'Color', [0 0 1 0.4], 'LineStyle', ':', 'LineWidth', 1.5);
    
    % Affichage dans la console adapté à la nouvelle échelle
    fprintf('Waypoint fixe : X=%.3f m, Y=%.3f m\n', pos(1)/1000, pos(2)/1000);
end

function drawTrajectory(fig, ax)
    wps = getappdata(fig, 'allWaypoints');
    drone_group = getappdata(fig, 'drone_group');
    vertical_line = getappdata(fig, 'vertical_line');
    x_base = getappdata(fig, 'x_base');
    y_base = getappdata(fig, 'y_base');
    altitude = getappdata(fig, 'altitude');
    altitude_aff = getappdata(fig, 'altitude_aff');
    v_moy = getappdata(fig, 'v_moy');
   
    if size(wps, 1) < 2
        msgbox('Veuillez fixer au moins 2 waypoints pour tracer une trajectoire.');
        return;
    end
    % ====================== 1. TRACÉ COMPLET DE LA TRAJECTOIRE ======================
    dec_x = [x_base, x_base]; dec_y = [y_base, y_base]; dec_z = [5, altitude];
    transit_dep_x = [x_base, wps(1,1)]; transit_dep_y = [y_base, wps(1,2)]; transit_dep_z = [altitude, altitude];
    mission_x = wps(:,1)'; mission_y = wps(:,2)'; mission_z = altitude * ones(1, size(wps,1));
    transit_ret_x = [wps(end,1), x_base]; transit_ret_y = [wps(end,2), y_base]; transit_ret_z = [altitude, altitude];
    att_x = [x_base, x_base]; att_y = [y_base, y_base]; att_z = [altitude, 5];
    traj_x = [dec_x, transit_dep_x(2:end), mission_x, transit_ret_x(2:end), att_x];
    traj_y = [dec_y, transit_dep_y(2:end), mission_y, transit_ret_y(2:end), att_y];
    traj_z = [dec_z, transit_dep_z(2:end), mission_z, transit_ret_z(2:end), att_z];
    plot3(ax, dec_x, dec_y, dec_z, 'b-', 'LineWidth', 2.5);
    plot3(ax, [x_base wps(1,1)], [y_base wps(1,2)], [altitude altitude], 'c-', 'LineWidth', 2);
    plot3(ax, mission_x, mission_y, mission_z, 'Color', [0.6 0 0.8], 'LineWidth', 3);
    plot3(ax, mission_x, mission_y, mission_z, 'wo', 'MarkerSize', 8, 'MarkerFaceColor', 'g', 'LineWidth', 1.5);
    plot3(ax, [wps(end,1) x_base], [wps(end,2) y_base], [altitude altitude], 'g-', 'LineWidth', 2);
    plot3(ax, att_x, att_y, att_z, 'r-', 'LineWidth', 2.5);
    title(ax, sprintf('Trajectoire validée - %d waypoints - Altitude %.2fm', size(wps,1), altitude_aff));
    drawnow;
    % ====================== 2. DÉCOLLAGE AVEC ORIENTATION INITIALE ======================
    initial_angle = atan2(wps(1,2) - y_base, wps(1,1) - x_base);
    takeoff_steps = 35;
    takeoff_z = linspace(5, altitude, takeoff_steps);
    for k = 1:takeoff_steps
        set(vertical_line, 'XData', [x_base, x_base], ...
                           'YData', [y_base, y_base], ...
                           'ZData', [0, takeoff_z(k)]);
        Tx = makehgtform('translate', [x_base, y_base, takeoff_z(k)]);
        Rz = makehgtform('zrotate', initial_angle);
        set(drone_group, 'Matrix', Tx * Rz);
        drawnow limitrate;
        pause(0.025);
    end
    % ====================== 3. ANIMATION FLUIDE ET VIRAGES FACES À LA PISTE ======================
    dt = 0.025;   
    traj_pts = [traj_x' traj_y' traj_z'];
    dist_pts = sqrt(sum(diff(traj_pts).^2, 2));
    dist_pts(dist_pts == 0) = 1e-6;
    temps_cum = [0; cumsum(dist_pts / v_moy)];
    
    t_start = temps_cum(2); 
    t_sim = t_start:dt:temps_cum(end);
    
    xi = interp1(temps_cum, traj_x', t_sim, 'linear');
    yi = interp1(temps_cum, traj_y', t_sim, 'linear');
    zi = interp1(temps_cum, traj_z', t_sim, 'linear');
    
    current_angle = initial_angle;
    
    for k = 1:length(xi)
        set(vertical_line, 'XData', [xi(k), xi(k)], ...
                           'YData', [yi(k), yi(k)], ...
                           'ZData', [0, zi(k)]);
        if k < length(xi)
            dx = xi(k+1) - xi(k); 
            dy = yi(k+1) - yi(k);
            if sqrt(dx^2 + dy^2) > 1e-3
                target_angle = atan2(dy, dx);
            else
                target_angle = current_angle;
            end
        else
            target_angle = current_angle;
        end
       
        angle_diff = target_angle - current_angle;
        angle_diff = atan2(sin(angle_diff), cos(angle_diff)); 
        
        if abs(angle_diff) > 0.01
            current_angle = current_angle + angle_diff * 0.25;
        else
            current_angle = target_angle;
        end
        
        Tx = makehgtform('translate', [xi(k), yi(k), zi(k)]);
        Rz = makehgtform('zrotate', current_angle);
        set(drone_group, 'Matrix', Tx * Rz);
        drawnow limitrate;
        pause(0.012);   
    end
    set(vertical_line, 'XData', [x_base, x_base], 'YData', [y_base, y_base], 'ZData', [0, 5]);
    fprintf('Mission terminée. %d waypoints parcourus.\n', size(wps,1));
end